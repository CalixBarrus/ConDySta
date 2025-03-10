

from hybrid.source_sink import MethodSignature


def test_from_smali_style_signature_taint_example():

    smali_signature = f"Lcom/example/taintinsertion/TaintInsertion;->taintStr0()Ljava/lang/String;"
    expected_java_signature = "<com.example.taintinsertion.TaintInsertion: java.lang.String taintStr0()>"

    method = MethodSignature.from_smali_style_signature(smali_signature)
    assert str(method) == expected_java_signature

    
    smali_signature = f"Lcom/example/taintinsertion/TaintInsertion;->taintObject0(Ljava/lang/Object;)Ljava/lang/Object;"
    expected_java_signature = "<com.example.taintinsertion.TaintInsertion: java.lang.Object taintObject0(java.lang.Object)>"

    method = MethodSignature.from_smali_style_signature(smali_signature)
    assert str(method) == expected_java_signature
