from main import db


PostCategory = db.Table('PostCategory', db.Model.metadata, 
                    db.Column('Post_id', db.Integer, db.ForeignKey('Post.id')), 
                    db.Column('Category_id', db.Integer, db.ForeignKey('Category.id')))


PostReply = db.Table('PostReply', db.Model.metadata, 
                    db.Column('Post_id', db.Integer, db.ForeignKey('Post.id')), 
                    db.Column('Reply_id', db.Integer, db.ForeignKey('Reply.id')))



class User(db.Model):
    __tablename__ = 'User'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.Text)
    email = db.Column(db.Text)
    password = db.Column(db.Text)

    user_post = db.relationship('Post', back_populates='post_user')
    notifications_user = db.relationship('Notification', back_populates='users_notification')
    # Comment
    users = db.relationship('Comment', back_populates='post')


class Reply(db.Model):
    __tablename__ = 'Reply'  
    id = db.Column(db.Integer, primary_key=True)
    reply = db.Column(db.Text)
    date = db.Column(db.Integer)

    posts_reply = db.relationship('Post', secondary=PostReply, back_populates='replies_post')


class Post(db.Model):
    __tablename__ = 'Post'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.Text)
    discussion = db.Column(db.Text)
    date = db.Column(db.Integer)
    comments = db.Column(db.Integer)
    user_id = db.Column(db.Integer, db.ForeignKey('User.id'))

    post_user = db.relationship('User', back_populates='user_post')
    replies_post = db.relationship('Reply', secondary=PostReply, back_populates='posts_reply')
    categories_post = db.relationship('Category', secondary=PostCategory, back_populates='posts_category')
    notifications_post = db.relationship('Notification', back_populates='posts_notification')
    # Comment
    posts = db.relationship('Comment', back_populates='user')


class Notification(db.Model):
    __tablename__ = 'Notification'
    id = db.Column(db.Integer, primary_key=True)
    sender = db.Column(db.Text)
    content = db.Column(db.Text)
    user_id = db.Column(db.Integer, db.ForeignKey('User.id'), nullable = False)
    post_id = db.Column(db.Integer, db.ForeignKey('Post.id'), nullable = False)

    users_notification = db.relationship('User', back_populates='notifications_user')
    posts_notification = db.relationship('Post', back_populates='notifications_post')


class Category(db.Model):
    __tablename__ = 'Category'
    id = db.Column(db.Integer, primary_key=True)
    topic = db.Column(db.Text)

    posts_category = db.relationship('Post', secondary=PostCategory, back_populates='categories_post')


class Comment(db.Model):
    __tablename__ = 'Comment'
    id = db.Column(db.Integer, primary_key=True)
    Post_id = db.Column(db.Integer, db.ForeignKey('Post.id'), nullable = True)
    User_id = db.Column(db.Integer, db.ForeignKey('User.id'), nullable = False)
    comment = db.Column(db.Text, nullable = False)

    user = db.relationship('Post', back_populates='posts')
    post = db.relationship('User', back_populates='users')