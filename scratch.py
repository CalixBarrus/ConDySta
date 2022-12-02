import xml.etree.ElementTree as ET

def main():
    tree = ET.parse('testfile.txt')
    root = tree.getroot()


if __name__ == '__main__':
    main()
