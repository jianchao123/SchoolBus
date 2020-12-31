from weixin import WeixinLogin

MINI_APP_ID = "wxe8eaaa37cd442ff9"
MINI_APP_SECRET = "eec6f8c6dfae6a56bcb1b4525250129b"


class MiniService(object):

    @staticmethod
    def get_login_status(code):
        wx_login = WeixinLogin(MINI_APP_ID, MINI_APP_SECRET)
        try:
            session_info = wx_login.jscode2session(code)
        except:
            return -10
        print(session_info)
        session_key = session_info.get('session_key')
        open_id = session_info.get('openid')
        user = UserProfile.query.filter(
            UserProfile.wx_open_id == open_id).first()

        code = "MINI " + open_id
        if user:
            is_new_user = False
            # 保存登录信息到redis
            k = MiniService.TOKEN_ID_KEY.format(code)
            cache.set(k, user.id)
            cache.expire(k, 60 * 60 * 2)
        else:
            is_new_user = True
            # 仅供sign_up_user使用
            mapping = dict(open_id=open_id, session_key=session_key)
            cache.hmset(code, mapping)
            cache.expire(code, 60)

        return {"is_new_user": is_new_user, "token": code}

    @staticmethod
    def sign_up_user(encrypted_data, iv, token):
        mapping = cache.hmget(token, "open_id", "session_key")
        if not mapping[0] or not mapping[1]:
            return -10

        pc = WXBizDataCrypt(conf.config['MINI_APP_ID'], str(mapping[1]))
        try:
            data = pc.decrypt(encrypted_data, iv)
        except:
            import traceback
            print traceback.format_exc()
            return -11
        mobile = data["purePhoneNumber"]
        user = UserProfile.query.filter(
            UserProfile.mobile == mobile).first()
        if user:
            user.wx_open_id = str(mapping[0])
            new_id = user.id
        else:
            user = UserProfile()
            user.password = md5_encrypt(mobile)
            user.mobile = mobile
            user.wx_open_id = str(mapping[0])
            user.username = mobile
            user.nickname = mobile
            user.is_open_face_rgz = 1
            user.email = '{}@wgx.com'.format(mobile)
            user.is_active = 1
            user.id_card = ''
            user.balance = Decimal(str(0.0))
            user.avatar = ''
            user.gender = 1
            user.birthday = date.today()
            user.company_id = 1 # 无感行

            db.session.add(user)
            db.session.flush()
            new_id = user.id

            # 保存登录信息到redis
            code = "MINI " + mapping[0]
            k = MiniService.TOKEN_ID_KEY.format(code)
            cache.set(k, new_id)
            cache.expire(k, 60 * 60 * 2)
        try:
            db.session.commit()
            return {"phone": mobile, "id": new_id}
        except SQLAlchemyError:
            db.session.rollback()
            return -2
        finally:
            db.session.close()