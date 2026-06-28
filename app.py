import os
from flask import Flask, send_from_directory
from flask_cors import CORS
from models import db, Post, User, Message, Report, Like, Comment
from routes import api_bp


app = Flask(__name__)
CORS(app)

# उदाहरणका लागि:
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'mp4', 'mov', 'avi'}

# फाइलहरू सेभ हुने फोल्डर 'uploads' बनाउने
UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://neondb_owner:npg_Gr9wWyqtEg3D@ep-small-queen-aozhzjn1-pooler.c-2.ap-southeast-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
app.register_blueprint(api_bp, url_prefix='/api')

# अपलोड भएका फाइलहरू एपमा देखाउन/तान्नको लागि Route
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
@app.route('/create-admin')
def create_admin_route():
    from werkzeug.security import generate_password_hash
    db.create_all() 
    
    admin_email = 'admin@suryodaya.com'
    user = User.query.filter_by(email=admin_email).first()
    
    if not user:
        new_admin = User(
            username='Admin', 
            email=admin_email, 
            password_hash=generate_password_hash('admin123'), 
            role='ADMIN'
        )
        db.session.add(new_admin)
        db.session.commit()
        return "<h1>✅ Admin created successfully on Live Server!</h1>"
    else:
        # यदि एड्मिन पहिले नै छ भने पासवर्ड रिसेट गरिदिने
        user.password_hash = generate_password_hash('admin123')
        db.session.commit()
        return "<h1>✅ Admin already exists. Password forcibly reset to admin123!</h1>"

if __name__ == '__main__':
    with app.app_context():
        db.create_all() 
    app.run(debug=True, port=5000)