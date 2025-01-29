
from typing import List

from intercept import smali
from intercept.smali import SmaliMethodInvocation


class AccessPath:
    # Format corresponds to a List<FieldInfo> in Snapshot.java

    class FieldInfo:
        # Copy of FieldInfo class in Snapshot.java
        fieldClassName: str
        fieldName: str

        def __init__(self, field: str):
            # Expects <{} {}> format
            field = field.strip('<>')
            self.fieldClassName = field.split(' ')[0]
            self.fieldName = field.split(' ')[1]

        def __str__(self):
            return f"<{self.fieldClassName} {self.fieldName}>"
        
        def __eq__(self, other):
            if isinstance(other, AccessPath.FieldInfo):
                return (self.fieldClassName == other.fieldClassName and
                        self.fieldName == other.fieldName)
            return False

        def __hash__(self):
            return hash((self.fieldClassName, self.fieldName))
        
        def get_smali_type(self):
            return smali.java_type_to_smali_type(self.fieldClassName)

    fields: List[FieldInfo]

    def __init__(self, access_path: str):
        
        self.fields = self._parse_access_path(access_path)

    def __str__(self):
        return f"[{", ".join(str(field) for field in self.fields)}]"
    
    def __eq__(self, other):
        if isinstance(other, AccessPath):
            return self.fields == other.fields
        return False

    def __hash__(self):
        return hash(tuple(self.fields))

    @staticmethod
    def _parse_access_path(access_path: str) -> List[FieldInfo]:
        # Example: [<java.lang.String .>, <{} {}>]
        access_path = access_path.strip('[]')
        entries = [AccessPath.FieldInfo(entry) for entry in access_path.split(', ')]
        return entries
    

