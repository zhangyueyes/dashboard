#-*- coding:utf-8 -*-
import json
from flask import request, g, abort, render_template
from rrd import app
from rrd.view.utils import require_login, require_login_json 
from rrd.model.user import User

@app.route("/user/about/<int:user_id>", methods=["GET",])
@require_login()
def user_info(user_id):
    if request.method == "GET":
        user = User.get_by_id(user_id)
        return render_template("user/about.html", **locals())

@app.route("/user/profile", methods=["GET", "POST"])
@require_login()
def user_profile():
    if request.method == "GET":
        current_user = g.user
        return render_template("user/profile.html", **locals())

    if request.method == "POST":
        ret = {"msg":""}

        cnname = request.form.get("cnname", "")
        email = request.form.get("email", "")
        im = request.form.get("im", "")
        phone = request.form.get("phone", "")
        qq = request.form.get("qq", "")

        d = {
                "cnname": cnname,
                "email": email,
                "im": im,
                "phone": phone,
                "qq": qq,
        }

        try:
            User.update_user_profile(d)
        except Exception as e:
            ret['msg'] = str(e)

        return json.dumps(ret)

@app.route("/user/chpwd", methods=["POST", ])
@require_login_json()
def user_change_passwd():
    if request.method == "POST":
        ret = {"msg": ""}

        old_password = request.form.get("old_password", "")
        new_password = request.form.get("new_password", "")
        repeat_password = request.form.get("repeat_password", "")
        if not (old_password and new_password and repeat_password):
            ret["msg"] = "some form item missing"
            return json.dumps(ret)

        if new_password != repeat_password:
            ret["msg"] = "repeat and new password not equal"
            return json.dumps(ret)

        try:
            User.change_user_passwd(old_password, new_password)
        except Exception as e:
            ret['msg'] = str(e)

        return json.dumps(ret)
        
@app.route("/user/list", methods=["GET",])
@require_login()
def user_list():
    if request.method == "GET":
        query_term = request.args.get("query", "")
        limit = g.limit or 20
        page = g.page or 1
        users = User.get_users(query_term, limit, page)
        return render_template("user/list.html", **locals())

@app.route("/user/query", methods=["GET",])
@require_login_json()
def user_query():
    if request.method == "GET":
        query_term = request.args.get("query", "")
        limit = g.limit or 20
        page = g.page or 1

        ret = {"users":[], "msg":""}
        try:
            users = User.get_users(query_term, limit, page)
            ret['users'] = [u.dict() for u in users]
        except Exception as e:
            ret['msg'] = str(e)
            logger.error(str(e))

        return json.dumps(ret)

#anyone can create a new user
@app.route("/user/create", methods=["GET", "POST"])
@require_login()
def user_create():
    if request.method == "GET":
        return render_template("user/create.html", **locals())
    
    if request.method == "POST":
        ret = {"msg":""}

        name = request.form.get("name", "")
        cnname = request.form.get("cnname", "")
        password = request.form.get("password", "")
        email = request.form.get("email", "")
        phone = request.form.get("phone", "")
        im = request.form.get("im", "")
        qq = request.form.get("qq", "")

        if not name or not cnname or not password or not email:
            ret["msg"] = "not all form item entered"
            return json.dumps(ret)
        
        try:
            User.create_user(name, cnname, password, email, phone, im, qq)
        except Exception as e:
            ret['msg'] = str(e)

        return json.dumps(ret)

##admin
@app.route("/admin/user/<int:user_id>/edit", methods=["GET", "POST"])
@require_login()
def admin_user_edit(user_id):
    if request.method == "GET":
        if not (g.user.is_admin() or g.user.is_root()):
            abort(403, "no such privilege")

        user = User.get_by_id(user_id)
        if not user:
            abort(404, "no such user where id=%s" % user_id)

        return render_template("user/edit.html", **locals())
    
    if request.method == "POST":
        ret = {"msg":""}

        if not (g.user.is_admin() or g.user.is_root()):
            ret["msg"] = "no such privilege"
            return json.dumps(ret)

        user_id = request.form.get("id", "")
        cnname = request.form.get("cnname", "")
        email = request.form.get("email", "")
        phone = request.form.get("phone", "")
        im = request.form.get("im", "")
        qq = request.form.get("qq", "")

        d = {
            "user_id": user_id, "cnname": cnname, "email": email, "phone": phone, "im": im, "qq": qq,
        }
        try:
            User.admin_update_user_profile(d)
        except Exception as e:
            ret['msg'] = str(e)

        return json.dumps(ret)

@app.route("/admin/user/<int:user_id>/chpwd", methods=["POST", ])
@require_login_json()
def admin_user_change_password(user_id):
    if request.method == "POST":
        ret = {"msg": ""}

        if not (g.user.is_admin or g.user.is_root()):
            ret["msg"] = "you do not have permissions"
            return json.dumps(ret)

        password = request.form.get("password")
        if not password:
            ret["msg"] = "no password entered"
            return json.dumps(ret)

        try:
            User.admin_change_user_passwd(user_id, password)
        except Exception as e:
            ret['msg'] = str(e)

        return json.dumps(ret)

@app.route("/admin/user/<int:user_id>/role", methods=["POST", ])
@require_login_json()
def admin_user_change_role(user_id):
    if request.method == "POST":
        ret = {"msg": ""}

        if not (g.user.is_admin or g.user.is_root()):
            ret["msg"] = "you do not have permissions"
            return json.dumps(ret)

        role = str(request.form.get("role", ""))
        if not role or role not in ['1', '0']:
            ret["msg"] = "invalid role"
            return json.dumps(ret)

        admin = "yes" if role == '1' else "no"
        try:
            User.admin_change_user_role(user_id, admin)
        except Exception as e:
            ret['msg'] = str(e)

        return json.dumps(ret)

@app.route("/admin/user/<int:user_id>/delete", methods=["POST", ])
@require_login_json()
def admin_user_delete(user_id):
    if request.method == "POST":
        ret = {"msg": ""}

        if not (g.user.is_admin or g.user.is_root()):
            ret["msg"] = "you do not have permissions"
            return json.dumps(ret)

        try:
            User.admin_delete_user(user_id)
        except Exception as e:
            ret['msg'] = str(e)

        return json.dumps(ret)