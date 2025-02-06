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
