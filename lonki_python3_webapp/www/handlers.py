#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'lonki'

' url handlers '

import re,time,json,logging,hashlib,base64,asyncio

from aiohttp import web

from coroweb import get,post

from models import User,Comment,Blog,next_id

from apis import APIValueError, APIResourceNotFoundError,APIError,APIPermissionError,Page

from config import configs

import markdown2

COOKIE_NAME = 'lonkisession'
_COOKIE_KEY = configs.session.secret

_RE_EMAIL = re.compile(r'^[a-z0-9\.\-\_]+\@[a-z0-9\-\_]+(\.[a-z0-9\-\_]+){1,4}$')
_RE_SHA1 = re.compile(r'^[0-9a-f]{40}$')

#检查用户
def check_admin(request):
    if request.__user__ is None or not request.__user__.admin:
        raise APIPermissionError()

def get_page_index(page_str):
    p = 1
    try:
        p = int(page_str)
    except ValueError as e:
        pass
    if p < 1:
        p = 1
    return p

#create cookie
def user2cookie(user, max_age):
    '''
    Generate cookie str by user.
    '''

    # build cookie string by: id-expires-sha1
    expires = str(int(time.time() + max_age))
    s = '%s-%s-%s-%s' %(user.id,user.passwd,expires,_COOKIE_KEY)
    L = [user.id,expires,hashlib.sha1(s.encode('utf-8')).hexdigest()]
    return '-'.join(L)

#解密cookie:
async def cookie2user(cookie_str):
    '''
       Parse cookie and load user if cookie is valid.
    '''
    if not cookie_str:
        return None
    try:
        L = cookie_str.split('-')
        if len(L) != 3:
            return None
        uid,expires,sha1 = L
        if int(expires) < time.time():
            return None
        user = await User.find(uid)
        if user is None:
            return None
        s = '%s-%s-%s-%s' % (user.id, user.passwd, expires, _COOKIE_KEY)
        if sha1 != hashlib.sha1(s.encode('utf-8')).hexdigest():
            logging.info('invalid sha1')
            return None
        user.passwd = '******'
        return user
    except Exception as e:
        logging.exception(e)
        return None

def text2html(text):
    lines = map(lambda s: '<p>%s</p>' % s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;'),filter(lambda s: s.strip() != '', text.split('\n')))
    return ''.join(lines)

#首页
@get('/')
async def index(*,page='1'):
    page_index = get_page_index(page)
    num = await Blog.findNumber('count(id)')
    page = Page(num,page_index)
    if num == 0:
        blogs = []
    else:
        blogs = await Blog.findAll(orderBy='created_at desc',limit=(page.offset,page.limit))
    return {
        '__template__':'blogs.html',
        'page':page,
        'blogs':blogs
    }

#获取日志详情
@get('/blog/{id}')
async def get_blog(id):
    blog = await Blog.find(id)
    if blog is None:
        raise APIResourceNotFoundError('Blog')
    comments = await Comment.findAll('blog_id=?',[id],orderBy='created_at desc')
    for c in comments:
        c.html_content = text2html(c.content)
    blog.html_content = markdown2.markdown(blog.content)
    return {
        '__template__': 'blog.html',
        'blog': blog,
        'comments': comments
    }

#创建日志评论
@post('/api/blogs/{id}/comments')
async def api_create_comment(id,request,*,content):
    user = request.__user__
    if user is None:
        raise APIPermissionError('Please signin first.')
    if not content or not content.strip():
        raise APIValueError('Please enter content.')
    blog = await Blog.find(id)
    if blog is None:
        raise APIResourceNotFoundError('Blog')
    comment = Comment(blog_id=blog.id,user_id=blog.user_id,user_name=user.name,user_image=user.image,content=content.strip())
    await comment.save()
    return comment

#注册
@get('/register')
def register():
    return {
        '__template__' : 'register.html'
    }

#登录
@get('/signin')
def signin():
    return {
        '__template__' : 'signin.html'
    }

#退出
@get('/signout')
def signout(request):
    referer = request.headers.get('Referer')
    r = web.HTTPFound(referer or '/')
    r.set_cookie(COOKIE_NAME,'-delete-',max_age=0,httponly=True)
    logging.info('user signed out.')
    return r

#管理员页面
@get('/manage/')
def manage():
    return 'redirect:/manage/comments'

#评论管理
@get('/manage/comments')
def manage_comments(*,page='1'):
    return {
        '__template__': 'manage_comments.html',
        'page_index': get_page_index(page)
    }

#日志管理
@get('/manage/blogs')
def manage_blogs(*,page='1'):
    return {
        '__template__' : 'manage_blogs.html',
        'page_index' : get_page_index(page)
    }

#创建日志
@get('/manage/blogs/create')
def manage_create_blog():
    return {
        '__template__' : 'manage_blog_edit.html',
        'id' : '',
        'action' : '/api/blogs'
    }

#修改日志
@get('/manage/blogs/edit')
def manage_edit_blog(*,id):
    return {
        '__template__':'manage_blog_edit.html',
        'id' : id,
        'action':'/api/blogs/%s' % id
    }

#评论列表
@get('/api/comments')
async def api_comments(*,page='1'):
    page_index = get_page_index(page)
    num = await Comment.findNumber('count(id)')
    p = Page(num,page_index)
    if num == 0:
        return dict(page=p,comments=())
    comments = await Comment.findAll(orderBy='created_at desc',limit=(p.offset,p.limit))
    return dict(page=p,comments=comments)

#删除评论
@post('/api/comments/{id}/delete')
async def api_delete_comments(id,request):
    check_admin(request)
    comment = await Comment.find(id)
    if comment is None:
        raise APIResourceNotFoundError('Comment')
    await comment.remove()
    return dict(id=id)

#用户管理
@get('/manage/users')
def manage_users(*,page='1'):
    return {
        '__template__' : 'manage_users.html',
        'page_index' : get_page_index(page)
    }

#用户注册
@post('/api/users')
async def api_register_user(*,email,name,passwd):
    if not name or not name.strip():
        raise APIValueError('name')
    if not email or not _RE_EMAIL.match(email):
        raise APIValueError('email')
    if not passwd or not _RE_SHA1.match(passwd):
        raise APIValueError('passwd')
    users = await User.findAll('email=?',[email])
    if len(users) > 0:
        raise APIError('register:failed','email','Email is already in use.')
    uid = next_id()
    sha1_passwd = '%s:%s' %(uid,passwd)
    user = User(id=uid,name=name.strip(),email=email,passwd=hashlib.sha1(sha1_passwd.encode('utf-8')).hexdigest(),image='http://www.gravatar.com/avatar/%s?d=mm&s=120' % hashlib.md5(email.encode('utf-8')).hexdigest() )
    await user.save()
    #make session cookie
    r = web.Response()
    r.set_cookie(COOKIE_NAME,user2cookie(user,86400),max_age=86400,httponly=True)
    user.passwd = '******'
    r.content_type = 'application/json'
    r.body = json.dumps(user,ensure_ascii=False).encode('utf-8')
    return r

#用户权限验证
@post('/api/authenticate')
async def authenticate(*,email,passwd):
    if not email:
        raise APIValueError('email','Invalid email.')
    if not passwd:
        raise APIValueError('passwd','Invalid password.')
    users = await User.findAll('email=?',[email])
    if len(users) == 0:
        raise APIValueError('email','Email not exist.')
    user = users[0]

    # check passwd:
    sha1 = hashlib.sha1()
    sha1.update(user.id.encode('utf-8'))
    sha1.update(b':')
    sha1.update(passwd.encode('utf-8'))
    if user.passwd != sha1.hexdigest():
        raise APIValueError('passwd','Invalid password.')

    # authenticate ok, set cookie:
    r = web.Response()
    r.set_cookie(COOKIE_NAME,user2cookie(user,86400),max_age=86400,httponly=True)
    r.content_type = 'application/json'
    r.body = json.dumps(user, ensure_ascii=False).encode('utf-8')
    return r

#日志列表
@get('/api/blogs')
async def api_blogs(*,page='1'):
    page_index = get_page_index(page)
    num = await Blog.findNumber('count(id)')
    p = Page(num,page_index)
    if num == 0:
        return dict(page=p,blogs=())
    blogs = await Blog.findAll(orderBy='created_at desc',limit=(p.offset,p.limit))
    return dict(page=p,blogs=blogs)

#用户列表
@get('/api/users')
async def api_users(*,page='1'):
    page_index = get_page_index(page)
    num = await User.findNumber('count(id)')
    p = Page(num,page_index)
    if num == 0:
        return dict(page=p,users=())
    users = await User.findAll(orderBy='created_at desc',limit=(p.offset,p.limit))
    for user in users:
        user.passwd = '******'
    return dict(page=p,users=users)


#获取日志 --修改日志页面用
@get('/api/blogs/{id}')
async def api_get_blog(*,id):
    blog = await Blog.find(id)
    return blog

#创建日志
@post('/api/blogs')
async def api_create_blog(request,*,name,summary,content):
    check_admin(request)
    if not name or not name.strip():
        raise APIValueError('name','name cannot be empty.')
    if not summary or not summary.strip():
        raise APIValueError('summary','summary cannot by empty.')
    if not content or not content.strip():
        raise APIValueError('content','content cannot by empty.')

    blog = Blog(user_id=request.__user__.id,user_name=request.__user__.name,user_image=request.__user__.image,name = name.strip(),summary=summary.strip(),content=content.strip())
    await blog.save()
    return blog

#修改日志
@post('/api/blogs/{id}')
async def api_update_blog(id,request,*,name,summary,content):
    check_admin(request)
    blog = await  Blog.find(id)
    if not name or not name.strip():
        raise APIValueError('name','name cannot be empty.')
    if not summary or not summary.strip():
        raise APIValueError('summary','summary cannot by empty.')
    if not content or not content.strip():
        raise APIValueError('content','content cannot by empty.')

    blog.name = name.strip()
    blog.summary = summary.strip()
    blog.content = content.strip()
    await blog.update()
    return blog

#删除日志
@post('/api/blogs/{id}/delete')
async def api_delete_blog(id,request):
    check_admin(request)
    blog = await  Blog.find(id)
    if blog is None:
        raise APIResourceNotFoundError('Blog')
    await blog.remove()
    return dict(id=id)