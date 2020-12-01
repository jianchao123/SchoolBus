# coding:utf-8
import oss2
import config


class OssOperation(object):

    def __init__(self):
        auth = oss2.Auth(config.OSSAccessKeyId, config.OSSAccessKeySecret)
        self.bucket = oss2.Bucket(auth, config.OSSEndpoint, 'wgxing-device')

    def delete_prefix_file(self):
        prefix = "people/face/"
        for obj in oss2.ObjectIterator(self.bucket, prefix=prefix):
            self.bucket.delete_object(obj.key)


if __name__ == '__main__':
    t = OssOperation()
    t.delete_prefix_file()