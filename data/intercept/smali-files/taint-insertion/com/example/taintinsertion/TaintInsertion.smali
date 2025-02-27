.class public Lcom/example/taintinsertion/TaintInsertion;
.super Ljava/lang/Object;
.source "TaintInsertion.java"


# direct methods
.method public constructor <init>()V
    .locals 0

    .line 3
    invoke-direct {p0}, Ljava/lang/Object;-><init>()V

    return-void
.end method

.method public static taint()Ljava/lang/String;
    .locals 1

    .line 5
    const-string v0, "secret"

    return-object v0
.end method

.method public static taintObject1(Ljava/lang/Object;)Ljava/lang/Object;
    .locals 0
    .param p0, "o"    # Ljava/lang/Object;

    .line 49
    return-object p0
.end method

.method public static taintObject10(Ljava/lang/Object;)Ljava/lang/Object;
    .locals 0
    .param p0, "o"    # Ljava/lang/Object;

    .line 85
    return-object p0
.end method

.method public static taintObject2(Ljava/lang/Object;)Ljava/lang/Object;
    .locals 0
    .param p0, "o"    # Ljava/lang/Object;

    .line 53
    return-object p0
.end method

.method public static taintObject3(Ljava/lang/Object;)Ljava/lang/Object;
    .locals 0
    .param p0, "o"    # Ljava/lang/Object;

    .line 57
    return-object p0
.end method

.method public static taintObject4(Ljava/lang/Object;)Ljava/lang/Object;
    .locals 0
    .param p0, "o"    # Ljava/lang/Object;

    .line 61
    return-object p0
.end method

.method public static taintObject5(Ljava/lang/Object;)Ljava/lang/Object;
    .locals 0
    .param p0, "o"    # Ljava/lang/Object;

    .line 65
    return-object p0
.end method

.method public static taintObject6(Ljava/lang/Object;)Ljava/lang/Object;
    .locals 0
    .param p0, "o"    # Ljava/lang/Object;

    .line 69
    return-object p0
.end method

.method public static taintObject7(Ljava/lang/Object;)Ljava/lang/Object;
    .locals 0
    .param p0, "o"    # Ljava/lang/Object;

    .line 73
    return-object p0
.end method

.method public static taintObject8(Ljava/lang/Object;)Ljava/lang/Object;
    .locals 0
    .param p0, "o"    # Ljava/lang/Object;

    .line 77
    return-object p0
.end method

.method public static taintObject9(Ljava/lang/Object;)Ljava/lang/Object;
    .locals 0
    .param p0, "o"    # Ljava/lang/Object;

    .line 81
    return-object p0
.end method

.method public static taintStr1()Ljava/lang/String;
    .locals 1

    .line 9
    const-string v0, "secret1"

    return-object v0
.end method

.method public static taintStr10()Ljava/lang/String;
    .locals 1

    .line 45
    const-string v0, "secret10"

    return-object v0
.end method

.method public static taintStr2()Ljava/lang/String;
    .locals 1

    .line 13
    const-string v0, "secret2"

    return-object v0
.end method

.method public static taintStr3()Ljava/lang/String;
    .locals 1

    .line 17
    const-string v0, "secret3"

    return-object v0
.end method

.method public static taintStr4()Ljava/lang/String;
    .locals 1

    .line 21
    const-string v0, "secret4"

    return-object v0
.end method

.method public static taintStr5()Ljava/lang/String;
    .locals 1

    .line 25
    const-string v0, "secret5"

    return-object v0
.end method

.method public static taintStr6()Ljava/lang/String;
    .locals 1

    .line 29
    const-string v0, "secret6"

    return-object v0
.end method

.method public static taintStr7()Ljava/lang/String;
    .locals 1

    .line 33
    const-string v0, "secret7"

    return-object v0
.end method

.method public static taintStr8()Ljava/lang/String;
    .locals 1

    .line 37
    const-string v0, "secret8"

    return-object v0
.end method

.method public static taintStr9()Ljava/lang/String;
    .locals 1

    .line 41
    const-string v0, "secret9"

    return-object v0
.end method
