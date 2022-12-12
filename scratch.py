import xml.etree.ElementTree as ET

def flowdroid_xml_output_test():
    parser = ET.XMLParser(encoding="utf-8")
    xmlFilePath = 'flowdroid_xml_output.xml'
    tree = ET.parse(xmlFilePath, parser=parser)

    root = tree.getroot()

    for child in root:
        print(child.tag, child.attrib, child.text)
        for grandchild in child:
            print(grandchild.tag, grandchild.attrib, grandchild.text)
            for ggrandchild in grandchild:
                print(ggrandchild.tag, ggrandchild.attrib, ggrandchild.text)

if __name__ == '__main__':
    flowdroid_xml_output_test()
