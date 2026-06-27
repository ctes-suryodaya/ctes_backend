import os
import random
from flask import Blueprint, jsonify, request, current_app
from werkzeug.utils import secure_filename
from sqlalchemy import or_
from models import db, Post, User, Message, Report, Like, Comment
import cloudinary
import cloudinary.uploader
from cloudinary.utils import cloudinary_url

# तपाईंले अघि कपी गरेका विवरणहरू यहाँ राख्नुहोस्
cloudinary.config( 
  cloud_name = "uclrfhkv", 
  api_key = "181254968853869", 
  api_secret = "GrHY3yMPGZGJ__SoO02mse-ljeY",
  secure = True
)

api_bp = Blueprint('api', __name__)

# १. सबै पोस्टहरू हेर्ने वा कीवर्डको आधारमा खोज्ने API (Search Feature)
@api_bp.route('/posts', methods=['GET'])
def get_posts():
    search_query = request.args.get('search', '')
    
    if search_query:
        # यदि केही सर्च गरेको छ भने सर्च नतिजा मात्र दिने
        posts = Post.query.filter(Post.title.ilike(f'%{search_query}%') | Post.content.ilike(f'%{search_query}%')).all()
    else:
        # सर्च नगरेको बेला (Home Screen मा) सबै पोष्ट तान्ने
        posts = Post.query.all()

    result = []
    for post in posts:
        admin = User.query.get(post.admin_id)
        likes_count = Like.query.filter_by(post_id=post.id).count()
        comments_count = Comment.query.filter_by(post_id=post.id).count()

        result.append({
            'id': post.id,
            'title': post.title,
            'content': post.content,
            'media_url': post.media_url,
            'created_at': post.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            'author': admin.username if admin else 'Unknown',
            'likes_count': likes_count,
            'comments_count': comments_count
        })

    # यदि सर्च गरेको होइन (अर्थात होमस्क्रिन हो) भने Algorithm लगाउने
    if not search_query:
        for item in result:
            # १ लाइक = २ पोइन्ट, १ कमेन्ट = ३ पोइन्ट 
            popularity_score = (item['likes_count'] * 2) + (item['comments_count'] * 3)
            
            # हरेक पटक रिफ्रेस गर्दा फरक देखाउन ० देखि २० सम्मको Random नम्बर जोड्ने
            random_factor = random.randint(0, 20) 
            
            # अन्तिम स्कोर
            item['feed_score'] = popularity_score + random_factor

        # सबैभन्दा धेरै feed_score भएकोलाई सबैभन्दा माथि (Descending) राख्ने
        result.sort(key=lambda x: x.get('feed_score', 0), reverse=True)

    return jsonify({'success': True, 'data': result}), 200

# २. सुरुमा एउटा Admin User बनाउन सजिलोको लागि (Setup API)
@api_bp.route('/init-admin', methods=['GET'])
def init_admin():
    admin = User.query.filter_by(username='Suryodaya_Admin').first()
    
    if not admin:
        new_admin = User(
            username='Suryodaya_Admin',
            email='info@suryodaya.gov.np',
            password_hash='secret_hash', 
            role='ADMIN'
        )
        db.session.add(new_admin)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Admin created successfully!', 'admin_id': new_admin.id}), 201
        
    return jsonify({'success': True, 'message': 'Admin already exists!', 'admin_id': admin.id}), 200

# ३. नयाँ पोस्ट राख्ने API (फाइल अपलोड सुविधा सहित)
# --- पोष्ट बनाउने र मिडिया Cloudinary मा पठाउने API ---
@api_bp.route('/posts', methods=['POST'])
def create_post():
    title = request.form.get('title')
    content = request.form.get('content')
    admin_id = request.form.get('admin_id') # वा तपाईंले जसरी admin_id लिनुभएको छ
    
    # फाइल लिने
    file = request.files.get('file') 
    media_url = ""

    if file:
        # यहाँ छ जादु! लोकल फोल्डरको साटो सिधै Cloudinary मा अपलोड
        # resource_type="auto" ले गर्दा यसले फोटो र भिडियो दुवै आफैँ चिनेर अपलोड गर्छ
        upload_result = cloudinary.uploader.upload(file, resource_type="auto")
        
        # अपलोड भएपछि Cloudinary ले दिने सुरक्षित (https) लिङ्क
        media_url = upload_result.get("secure_url")

    # डेटाबेसमा सेभ गर्ने
    new_post = Post(title=title, content=content, media_url=media_url, admin_id=admin_id)
    db.session.add(new_post)
    db.session.commit()

    return jsonify({'success': True, 'message': 'पोष्ट सफलतापूर्वक अपलोड भयो!'}), 201
# --- ४. एड्मिन लगइन API ---
@api_bp.route('/admin/login', methods=['POST'])
def admin_login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    # सूर्योदय नगरपालिकाको लागि एउटा आधिकारिक एड्मिन चेक
    if username == "admin_suryodaya" and password == "Suryodaya@2083":
        return jsonify({'success': True, 'message': 'Admin login successful!'}), 200
    return jsonify({'success': False, 'message': 'क्रेडिन्सियल मिलेन!'}), 401

# --- ५. च्याट / म्यासेज API ---
@api_bp.route('/messages', methods=['POST'])
def send_message():
    data = request.get_json()
    email = data.get('email')
    text = data.get('text')
    is_admin = data.get('is_from_admin', False)

    if not email or not text:
        return jsonify({'success': False, 'message': 'विवरण अपूर्ण भयो'}), 400

    new_msg = Message(sender_email=email, message_text=text, is_from_admin=is_admin)
    db.session.add(new_msg)
    db.session.commit()
    return jsonify({'success': True, 'message': 'Sent successfully!'}), 201

@api_bp.route('/messages', methods=['GET'])
def get_messages():
    # एड्मिन स्क्रिनमा सबै सन्देशहरू हेर्नका लागि
    msgs = Message.query.order_by(Message.created_at.asc()).all()
    result = [{
        'id': m.id,
        'email': m.sender_email,
        'text': m.message_text,
        'is_from_admin': m.is_from_admin,
        'time': m.created_at.strftime("%I:%M %p")
    } for m in msgs]
    return jsonify({'success': True, 'messages': result}), 200

# --- पोष्ट रिपोर्ट API ---
@api_bp.route('/reports', methods=['POST'])
def report_post():
    data = request.get_json()
    post_id = data.get('post_id')
    email = data.get('email')
    reason = data.get('reason')

    if not post_id or not reason:
        return jsonify({'success': False, 'message': 'विवरण अपूर्ण भयो'}), 400

    new_report = Report(post_id=post_id, reporter_email=email, reason=reason)
    db.session.add(new_report)
    db.session.commit()
    return jsonify({'success': True, 'message': 'Report Subnitted. We will ।'}), 201

@api_bp.route('/reports', methods=['GET'])
def get_reports():
    # एड्मिन प्यानलमा रिपोर्टहरू हेर्नका लागि
    reports = Report.query.order_by(Report.created_at.desc()).all()
    result = [{
        'id': r.id,
        'post_id': r.post_id,
        'email': r.reporter_email,
        'reason': r.reason,
        'time': r.created_at.strftime("%Y-%m-%d %H:%M")
    } for r in reports]
    return jsonify({'success': True, 'reports': result}), 200

    # --- ७. पोष्ट सम्पादन (Edit) र मेटाउने (Delete) API ---
@api_bp.route('/posts/<int:post_id>', methods=['DELETE'])
def delete_post(post_id):
    post = Post.query.get(post_id)
    if not post:
        return jsonify({'success': False, 'message': 'पोष्ट भेटिएन'}), 404
    
    db.session.delete(post)
    db.session.commit()
    return jsonify({'success': True, 'message': 'Successfully Deleted!'}), 200

@api_bp.route('/posts/<int:post_id>', methods=['PUT'])
def update_post(post_id):
    post = Post.query.get(post_id)
    if not post:
        return jsonify({'success': False, 'message': 'पोष्ट भेटिएन'}), 404
    
    data = request.get_json()
    if 'title' in data:
        post.title = data['title']
    if 'content' in data:
        post.content = data['content']
        
    db.session.commit()
    return jsonify({'success': True, 'message': 'Successfully Edited!'}), 200


    # --- ८. लाइक अन/अफ (Toggle Like) API ---
@api_bp.route('/posts/<int:post_id>/like', methods=['POST'])
def toggle_like(post_id):
    data = request.get_json()
    email = data.get('email')
    
    if not email:
        return jsonify({'success': False, 'message': 'Email is required'}), 400

    # प्रयोगकर्ताले पहिले नै लाइक गरेको छ कि छैन चेक गर्ने
    existing_like = Like.query.filter_by(post_id=post_id, user_email=email).first()
    
    if existing_like:
        db.session.delete(existing_like)
        db.session.commit()
        liked = False
    else:
        new_like = Like(post_id=post_id, user_email=email)
        db.session.add(new_like)
        db.session.commit()
        liked = True

    total_likes = Like.query.filter_by(post_id=post_id).count()
    return jsonify({'success': True, 'liked': liked, 'likes_count': total_likes}), 200


# --- ९. कमेन्ट थप्ने र हेर्ने API ---
@api_bp.route('/posts/<int:post_id>/comments', methods=['POST'])
def add_comment(post_id):
    data = request.get_json()
    email = data.get('email')
    content = data.get('content')

    if not email or not content:
        return jsonify({'success': False, 'message': 'विवरण अपूर्ण भयो'}), 400

    new_comment = Comment(post_id=post_id, user_email=email, content=content)
    db.session.add(new_comment)
    db.session.commit()
    return jsonify({'success': True, 'message': 'कमेन्ट थपियो!'}), 201


@api_bp.route('/posts/<int:post_id>/comments', methods=['GET'])
def get_comments(post_id):
    comments = Comment.query.filter_by(post_id=post_id).order_by(Comment.created_at.asc()).all()
    result = [{
        'id': c.id,
        'email': c.user_email,
        'content': c.content,
        'time': c.created_at.strftime("%I:%M %p")
    } for c in comments]
    return jsonify({'success': True, 'comments': result}), 200