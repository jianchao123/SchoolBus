# coding:utf-8
from sqlalchemy.exc import SQLAlchemyError
from database.db import db
from database.Iotproduct import Iotproduct
from database.Machine import Machine


class MachineService(object):

    @staticmethod
    def machine_list(device_iid, page, size):
        """机器列表"""
        db.session.commit()  # SELECT
        offset = (page - 1) * size
        query = db.session.query(Machine)
        if device_iid:
            query = query.filter(Machine.device_iid == device_iid)
        count = query.count()
        query = query.order_by(Machine.id.desc())
        results = query.offset(offset).limit(size).all()
        data = []
        for row in results:
            data.append({
                'id': row.id,
                'mac': row.mac,
                'product_id': row.product_id,
                'status': row.status,
                'product_key': row.product_key,
                'device_iid': row.device_iid,
                'dev_name': row.dev_name,
                'dev_secret': row.dev_secret
            })
        return {'results': data, 'count': count}

    @staticmethod
    def machine_update(pk, product_id):
        db.session.commit()  # SELECT
        machine = db.session.query(Machine).filter(
            Machine.id == pk).first()
        if not machine:
            return -1
        if product_id != machine.product_id:
            product = db.session.query(Iotproduct).filter(
                Iotproduct.id == product_id).first()
            if not product:
                return -1
            machine.product_id = product_id
            machine.status = 1
            machine.product_key = product.product_key
            machine.dev_name = ''
            machine.dev_secret = ''
        try:
            d = {'id': machine.id}
            db.session.commit()
            return d
        except SQLAlchemyError:
            db.session.rollback()
            return -2
        finally:
            db.session.close()

    @staticmethod
    def machine_add(pk, product_id, device_iid):
        db.session.commit()  # SELECT
        machine = Machine()
        product = db.session.query(Iotproduct).filter(
            Iotproduct.id == product_id).first()
        if not product:
            return -1
        machine.product_id = product_id
        machine.status = 1
        machine.product_key = product.product_key
        machine.dev_name = ''
        machine.dev_secret = ''
        machine.device_iid = device_iid
        try:
            d = {'id': machine.id}
            db.session.commit()
            return d
        except SQLAlchemyError:
            db.session.rollback()
            return -2
        finally:
            db.session.close()

    @staticmethod
    def newdev_info(mac):
        db.session.commit()  # SELECT
        machine = db.session.query(Machine).filter(
            Machine.mac == mac).first()
        if not machine:
            return -1
        product = db.session.query(Iotproduct).filter(
            Iotproduct.id == machine.product_id).first()

        data = {
            'product_key': product.product_key,
            'newdev_secret': product.newdev_secret,
            'newdev_name': product.newdev_name
        }
        return data
