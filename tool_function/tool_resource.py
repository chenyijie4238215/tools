

def create_rcc(res_dir, res_types, qrc_path, rcc_path):
    import os
    qrc_data = ""
    for parent, dirnames, filenames in os.walk(res_dir):
        for filename in filenames:
            if os.path.splitext(filename)[1] in res_types:
                path = os.path.join(parent, filename).replace("\\", '/')
                data = "<file>{}</file>\n".format(path)
                qrc_data += data
    qrc = "<RCC>\n<qresource prefix=\"/\">\n{}</qresource>\n</RCC>".format(qrc_data)
    with open(qrc_path, 'w') as f:
        f.write(qrc)
    os.system("{0} {1} -compress 9 -o {2}".format("pyrcc5", qrc_path, rcc_path))


def url_image(path):
    return path

def url_path(path):
    return path