import os
from PyQt5.QtCore import QCoreApplication, QDir

from tool_function.decorator import singleton


@singleton
class Resource(object):
    DIR_PATH = None
    QRC_PATH = None
    RCC_PATH = None
    TYPES = tuple()

    def url_image(self, path):
        # root_dir = QCoreApplication.applicationDirPath()
        root_dir = QDir.currentPath()
        path = os.path.join(root_dir, "res", path).replace("\\", "/")
        print(path)

    def url_qml(self, path):
        pass

    @staticmethod
    def create_rcc():
        import os
        qrc_data = ""
        for parent, dirnames, filenames in os.walk(Resource.DIR_PATH):
            for filename in filenames:
                if os.path.splitext(filename)[1] in Resource.TYPES:
                    path = os.path.join(parent, filename).replace("\\", '/')
                    data = "<file>{}</file>\n".format(path)
                    qrc_data += data
        qrc = "<RCC>\n<qresource prefix=\"/\">\n{}</qresource>\n</RCC>".format(qrc_data)
        # 生成资源目录文件
        with open(Resource.QRC_PATH, 'w') as f:
            f.write(qrc)
        # 生成资源文件
        os.system("{0} {1} -compress 9 -o {2}".format("pyrcc5", Resource.QRC_PATH, Resource.RCC_PATH))
