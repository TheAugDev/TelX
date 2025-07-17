import os
from flask import Flask, request, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from datetime import datetime, timezone
import hashlib
import hmac
import urllib.parse
import json
import base64
from urllib.parse import unquote
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__, static_folder='static')
CORS(app)

# Database configuration
DATABASE_URL = os.environ.get('DATABASE_URL')
if DATABASE_URL and DATABASE_URL.startswith('postgres://'):
    DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)

app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL or 'sqlite:///telx.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['BOT_TOKEN'] = os.environ.get('BOT_TOKEN', 'your_bot_token_here')

db = SQLAlchemy(app)

# Database Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    telegram_id = db.Column(db.BigInteger, unique=True, nullable=False)
    username = db.Column(db.String(80), nullable=True)
    first_name = db.Column(db.String(80), nullable=False)
    last_name = db.Column(db.String(80), nullable=True)
    language_code = db.Column(db.String(10), nullable=True)
    photo_url = db.Column(db.Text, nullable=True)
    bio = db.Column(db.Text, nullable=True, default='')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    posts = db.relationship('Post', backref='author', lazy=True, cascade='all, delete-orphan')
    likes = db.relationship('Like', backref='user', lazy=True, cascade='all, delete-orphan')
    comments = db.relationship('Comment', backref='author', lazy=True, cascade='all, delete-orphan')
    
    # Following relationships
    following = db.relationship('Follow', foreign_keys='Follow.follower_id', backref='follower', lazy=True, cascade='all, delete-orphan')
    followers = db.relationship('Follow', foreign_keys='Follow.following_id', backref='following', lazy=True, cascade='all, delete-orphan')

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    image_url = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    likes = db.relationship('Like', backref='post', lazy=True, cascade='all, delete-orphan')
    comments = db.relationship('Comment', backref='post', lazy=True, cascade='all, delete-orphan')

class Like(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (db.UniqueConstraint('user_id', 'post_id', name='unique_user_post_like'),)

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Follow(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    follower_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    following_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (db.UniqueConstraint('follower_id', 'following_id', name='unique_follow'),)

# Telegram WebApp authentication
def validate_telegram_data(init_data, bot_token):
    """Validate Telegram WebApp init data"""
    try:
        # Parse the init data
        parsed_data = urllib.parse.parse_qs(init_data)
        
        # Extract hash and remove it from data for validation
        received_hash = parsed_data.get('hash', [None])[0]
        if not received_hash:
            return None
            
        # Remove hash from data
        data_to_check = []
        for key, values in parsed_data.items():
            if key != 'hash':
                data_to_check.append(f"{key}={values[0]}")
        
        # Sort and join
        data_check_string = '\n'.join(sorted(data_to_check))
        
        # Create secret key
        secret_key = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
        
        # Calculate hash
        calculated_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
        
        # Verify hash
        if calculated_hash == received_hash:
            # Parse user data
            user_data = parsed_data.get('user', [None])[0]
            if user_data:
                return json.loads(unquote(user_data))
        
        return None
    except Exception as e:
        print(f"Validation error: {e}")
        return None

# Helper functions
def serialize_user(user, current_user_id=None):
    """Serialize user object for JSON response"""
    following_count = Follow.query.filter_by(follower_id=user.id).count()
    followers_count = Follow.query.filter_by(following_id=user.id).count()
    posts_count = Post.query.filter_by(user_id=user.id).count()
    
    is_following = False
    if current_user_id:
        is_following = Follow.query.filter_by(
            follower_id=current_user_id, 
            following_id=user.id
        ).first() is not None
    
    return {
        'id': user.id,
        'telegram_id': user.telegram_id,
        'username': user.username,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'full_name': f"{user.first_name} {user.last_name or ''}".strip(),
        'photo_url': user.photo_url,
        'bio': user.bio or '',
        'following_count': following_count,
        'followers_count': followers_count,
        'posts_count': posts_count,
        'is_following': is_following,
        'created_at': user.created_at.isoformat(),
        'handle': f"@{user.username}" if user.username else f"@user{user.telegram_id}"
    }

def serialize_post(post, current_user_id=None):
    """Serialize post object for JSON response"""
    likes_count = Like.query.filter_by(post_id=post.id).count()
    comments_count = Comment.query.filter_by(post_id=post.id).count()
    
    is_liked = False
    if current_user_id:
        is_liked = Like.query.filter_by(
            user_id=current_user_id, 
            post_id=post.id
        ).first() is not None
    
    return {
        'id': post.id,
        'content': post.content,
        'image_url': post.image_url,
        'author': serialize_user(post.author, current_user_id),
        'likes_count': likes_count,
        'comments_count': comments_count,
        'is_liked': is_liked,
        'created_at': post.created_at.isoformat(),
        'updated_at': post.updated_at.isoformat()
    }

def serialize_comment(comment, current_user_id=None):
    """Serialize comment object for JSON response"""
    return {
        'id': comment.id,
        'content': comment.content,
        'author': serialize_user(comment.author, current_user_id),
        'created_at': comment.created_at.isoformat(),
        'updated_at': comment.updated_at.isoformat()
    }

# Routes
@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory('static', filename)

@app.route('/api/auth', methods=['POST'])
def authenticate():
    """Authenticate user with Telegram WebApp init data"""
    data = request.get_json()
    init_data = data.get('initData')
    
    if not init_data:
        return jsonify({'error': 'No init data provided'}), 400
    
    # Validate Telegram data
    user_data = validate_telegram_data(init_data, app.config['BOT_TOKEN'])
    if not user_data:
        return jsonify({'error': 'Invalid Telegram data'}), 401
    
    # Find or create user
    telegram_id = user_data['id']
    user = User.query.filter_by(telegram_id=telegram_id).first()
    
    if not user:
        # Create new user
        user = User(
            telegram_id=telegram_id,
            username=user_data.get('username'),
            first_name=user_data['first_name'],
            last_name=user_data.get('last_name'),
            language_code=user_data.get('language_code'),
            photo_url=user_data.get('photo_url')
        )
        db.session.add(user)
        db.session.commit()
    else:
        # Update existing user data
        user.username = user_data.get('username')
        user.first_name = user_data['first_name']
        user.last_name = user_data.get('last_name')
        user.language_code = user_data.get('language_code')
        user.photo_url = user_data.get('photo_url')
        user.updated_at = datetime.utcnow()
        db.session.commit()
    
    return jsonify({
        'user': serialize_user(user, user.id),
        'message': 'Authentication successful'
    })

@app.route('/api/posts', methods=['GET'])
def get_posts():
    """Get posts with optional filtering"""
    # Get current user from auth header or query param
    current_user_id = request.headers.get('X-User-ID')
    if current_user_id:
        current_user_id = int(current_user_id)
    
    filter_type = request.args.get('filter', 'latest')
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 20))
    
    if filter_type == 'following' and current_user_id:
        # Get posts from followed users
        following_ids = [f.following_id for f in Follow.query.filter_by(follower_id=current_user_id).all()]
        query = Post.query.filter(Post.user_id.in_(following_ids))
    elif filter_type == 'trending':
        # Simple trending algorithm based on recent likes and comments
        # In production, you'd want a more sophisticated algorithm
        query = Post.query.join(Like).group_by(Post.id).order_by(
            db.func.count(Like.id).desc(),
            Post.created_at.desc()
        )
    else:
        # Latest posts
        query = Post.query
    
    # Order by creation date (most recent first)
    if filter_type != 'trending':
        query = query.order_by(Post.created_at.desc())
    
    # Paginate
    posts = query.paginate(
        page=page, 
        per_page=per_page, 
        error_out=False
    )
    
    return jsonify({
        'posts': [serialize_post(post, current_user_id) for post in posts.items],
        'has_next': posts.has_next,
        'has_prev': posts.has_prev,
        'page': page,
        'pages': posts.pages,
        'total': posts.total
    })

@app.route('/api/posts', methods=['POST'])
def create_post():
    """Create a new post"""
    current_user_id = request.headers.get('X-User-ID')
    if not current_user_id:
        return jsonify({'error': 'Authentication required'}), 401
    
    data = request.get_json()
    content = data.get('content', '').strip()
    image_url = data.get('image_url')
    
    if not content or len(content) > 280:
        return jsonify({'error': 'Content must be between 1 and 280 characters'}), 400
    
    post = Post(
        user_id=int(current_user_id),
        content=content,
        image_url=image_url
    )
    
    db.session.add(post)
    db.session.commit()
    
    return jsonify({
        'post': serialize_post(post, int(current_user_id)),
        'message': 'Post created successfully'
    }), 201

@app.route('/api/posts/<int:post_id>/like', methods=['POST'])
def toggle_like(post_id):
    """Toggle like on a post"""
    current_user_id = request.headers.get('X-User-ID')
    if not current_user_id:
        return jsonify({'error': 'Authentication required'}), 401
    
    current_user_id = int(current_user_id)
    post = Post.query.get_or_404(post_id)
    
    # Check if already liked
    existing_like = Like.query.filter_by(
        user_id=current_user_id,
        post_id=post_id
    ).first()
    
    if existing_like:
        # Unlike
        db.session.delete(existing_like)
        action = 'unliked'
    else:
        # Like
        like = Like(user_id=current_user_id, post_id=post_id)
        db.session.add(like)
        action = 'liked'
    
    db.session.commit()
    
    likes_count = Like.query.filter_by(post_id=post_id).count()
    
    return jsonify({
        'action': action,
        'likes_count': likes_count,
        'is_liked': action == 'liked'
    })

@app.route('/api/posts/<int:post_id>/comments', methods=['GET'])
def get_comments(post_id):
    """Get comments for a post"""
    current_user_id = request.headers.get('X-User-ID')
    if current_user_id:
        current_user_id = int(current_user_id)
    
    post = Post.query.get_or_404(post_id)
    comments = Comment.query.filter_by(post_id=post_id).order_by(Comment.created_at.desc()).all()
    
    return jsonify({
        'post': serialize_post(post, current_user_id),
        'comments': [serialize_comment(comment, current_user_id) for comment in comments]
    })

@app.route('/api/posts/<int:post_id>/comments', methods=['POST'])
def create_comment(post_id):
    """Create a comment on a post"""
    current_user_id = request.headers.get('X-User-ID')
    if not current_user_id:
        return jsonify({'error': 'Authentication required'}), 401
    
    data = request.get_json()
    content = data.get('content', '').strip()
    
    if not content or len(content) > 280:
        return jsonify({'error': 'Content must be between 1 and 280 characters'}), 400
    
    post = Post.query.get_or_404(post_id)
    
    comment = Comment(
        user_id=int(current_user_id),
        post_id=post_id,
        content=content
    )
    
    db.session.add(comment)
    db.session.commit()
    
    return jsonify({
        'comment': serialize_comment(comment, int(current_user_id)),
        'message': 'Comment created successfully'
    }), 201

@app.route('/api/users/<int:user_id>/follow', methods=['POST'])
def toggle_follow(user_id):
    """Toggle follow/unfollow a user"""
    current_user_id = request.headers.get('X-User-ID')
    if not current_user_id:
        return jsonify({'error': 'Authentication required'}), 401
    
    current_user_id = int(current_user_id)
    
    if current_user_id == user_id:
        return jsonify({'error': 'Cannot follow yourself'}), 400
    
    target_user = User.query.get_or_404(user_id)
    
    # Check if already following
    existing_follow = Follow.query.filter_by(
        follower_id=current_user_id,
        following_id=user_id
    ).first()
    
    if existing_follow:
        # Unfollow
        db.session.delete(existing_follow)
        action = 'unfollowed'
    else:
        # Follow
        follow = Follow(follower_id=current_user_id, following_id=user_id)
        db.session.add(follow)
        action = 'followed'
    
    db.session.commit()
    
    return jsonify({
        'action': action,
        'user': serialize_user(target_user, current_user_id)
    })

@app.route('/api/users', methods=['GET'])
def get_users():
    """Get users for discovery"""
    current_user_id = request.headers.get('X-User-ID')
    if current_user_id:
        current_user_id = int(current_user_id)
        # Get users that current user is not following
        following_ids = [f.following_id for f in Follow.query.filter_by(follower_id=current_user_id).all()]
        following_ids.append(current_user_id)  # Exclude self
        users = User.query.filter(~User.id.in_(following_ids)).limit(20).all()
    else:
        users = User.query.limit(20).all()
    
    return jsonify({
        'users': [serialize_user(user, current_user_id) for user in users]
    })

@app.route('/api/users/<int:user_id>', methods=['GET'])
def get_user_profile(user_id):
    """Get user profile with posts"""
    current_user_id = request.headers.get('X-User-ID')
    if current_user_id:
        current_user_id = int(current_user_id)
    
    user = User.query.get_or_404(user_id)
    posts = Post.query.filter_by(user_id=user_id).order_by(Post.created_at.desc()).all()
    
    return jsonify({
        'user': serialize_user(user, current_user_id),
        'posts': [serialize_post(post, current_user_id) for post in posts]
    })

@app.route('/api/user/profile', methods=['PUT'])
def update_profile():
    """Update current user's profile"""
    current_user_id = request.headers.get('X-User-ID')
    if not current_user_id:
        return jsonify({'error': 'Authentication required'}), 401
    
    user = User.query.get_or_404(int(current_user_id))
    data = request.get_json()
    
    # Update allowed fields
    if 'bio' in data:
        user.bio = data['bio'][:160]  # Limit bio length
    
    user.updated_at = datetime.utcnow()
    db.session.commit()
    
    return jsonify({
        'user': serialize_user(user, int(current_user_id)),
        'message': 'Profile updated successfully'
    })

# Initialize database
@app.before_request
def create_tables():
    if not hasattr(create_tables, '_initialized'):
        db.create_all()
        create_tables._initialized = True

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
