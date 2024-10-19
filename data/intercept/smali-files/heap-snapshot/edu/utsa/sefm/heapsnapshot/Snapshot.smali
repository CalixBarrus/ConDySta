.class public Ledu/utsa/sefm/heapsnapshot/Snapshot;
.super Ljava/lang/Object;
.source "Snapshot.java"


# annotations
.annotation system Ldalvik/annotation/MemberClasses;
    value = {
        Ledu/utsa/sefm/heapsnapshot/Snapshot$FieldInfo;
    }
.end annotation


# static fields
.field private static final CHECK_COLLECTION_ELEMENTS:Z = false

.field private static final CHECK_MAP_ELEMENTS:Z = false

.field private static final DEBUG_TAG:Ljava/lang/String; = "Snap-Debug"

.field private static final EXCLUDED_CLASSES:Ljava/util/List;
    .annotation system Ldalvik/annotation/Signature;
        value = {
            "Ljava/util/List<",
            "Ljava/lang/Class<",
            "*>;>;"
        }
    .end annotation
.end field

.field private static final HARNESSED_PII_PATTERN:Ljava/lang/String; = "\\*\\*\\*\\d{12}\\*\\*\\*"

.field private static final INSPECTION_DEPTH:I = 0x1

.field private static final PII:Ljava/util/List;
    .annotation system Ldalvik/annotation/Signature;
        value = {
            "Ljava/util/List<",
            "Ljava/lang/String;",
            ">;"
        }
    .end annotation
.end field

.field private static final TAG:Ljava/lang/String; = "Snapshot"

.field private static callId:I

.field private static isThreadCheckingObjectMap:Ljava/util/Map;
    .annotation system Ldalvik/annotation/Signature;
        value = {
            "Ljava/util/Map<",
            "Ljava/lang/Long;",
            "Ljava/lang/Boolean;",
            ">;"
        }
    .end annotation
.end field


# direct methods
.method static constructor <clinit>()V
    .locals 8

    .line 32
    const-string v0, "8901240197155182897"

    const-string v1, "355458061189396"

    const-string v2, "ZX1H22KHQK"

    const-string v3, "b91481e8-4bfc-47ce-82b6-728c3f6bff60"

    const-string v4, "f8:cf:c5:d1:02:e8"

    const-string v5, "f8:cf:c5:d1:02:e7"

    const-string v6, "tester.sefm@gmail.com"

    const-string v7, "Class-Deliver-Put-Earn-5"

    filled-new-array/range {v0 .. v7}, [Ljava/lang/String;

    move-result-object v0

    invoke-static {v0}, Ljava/util/Arrays;->asList([Ljava/lang/Object;)Ljava/util/List;

    move-result-object v0

    sput-object v0, Ledu/utsa/sefm/heapsnapshot/Snapshot;->PII:Ljava/util/List;

    .line 36
    const/4 v0, 0x4

    new-array v0, v0, [Ljava/lang/Class;

    const-class v1, Ljava/lang/Integer;

    const/4 v2, 0x0

    aput-object v1, v0, v2

    const/4 v1, 0x1

    const-class v3, Ljava/lang/Long;

    aput-object v3, v0, v1

    const/4 v1, 0x2

    const-class v3, Ljava/lang/Double;

    aput-object v3, v0, v1

    const/4 v1, 0x3

    const-class v3, Ljava/lang/Boolean;

    aput-object v3, v0, v1

    invoke-static {v0}, Ljava/util/Arrays;->asList([Ljava/lang/Object;)Ljava/util/List;

    move-result-object v0

    sput-object v0, Ledu/utsa/sefm/heapsnapshot/Snapshot;->EXCLUDED_CLASSES:Ljava/util/List;

    .line 40
    sput v2, Ledu/utsa/sefm/heapsnapshot/Snapshot;->callId:I

    .line 42
    new-instance v0, Ljava/util/HashMap;

    invoke-direct {v0}, Ljava/util/HashMap;-><init>()V

    sput-object v0, Ledu/utsa/sefm/heapsnapshot/Snapshot;->isThreadCheckingObjectMap:Ljava/util/Map;

    return-void
.end method

.method public constructor <init>()V
    .locals 0

    .line 23
    invoke-direct {p0}, Ljava/lang/Object;-><init>()V

    return-void
.end method

.method public static checkObjectForPII(Ljava/lang/Object;Ljava/lang/String;)I
    .locals 13
    .param p0, "instance"    # Ljava/lang/Object;
    .param p1, "invocationDescription"    # Ljava/lang/String;

    .line 128
    const/4 v0, 0x0

    .line 129
    .local v0, "localCallId":I
    const-class v1, Ledu/utsa/sefm/heapsnapshot/Snapshot;

    monitor-enter v1

    .line 130
    :try_start_0
    sget v2, Ledu/utsa/sefm/heapsnapshot/Snapshot;->callId:I

    const/4 v3, 0x1

    add-int/2addr v2, v3

    sput v2, Ledu/utsa/sefm/heapsnapshot/Snapshot;->callId:I

    .line 131
    move v0, v2

    .line 132
    monitor-exit v1
    :try_end_0
    .catchall {:try_start_0 .. :try_end_0} :catchall_0

    .line 136
    const/16 v1, 0x64

    .line 137
    .local v1, "div":I
    rem-int v2, v0, v1

    if-nez v2, :cond_0

    .line 138
    const-string v2, "Snap-Debug"

    new-instance v4, Ljava/lang/StringBuilder;

    invoke-direct {v4}, Ljava/lang/StringBuilder;-><init>()V

    const-string v5, "Calls to checkObjectForPII :"

    invoke-virtual {v4, v5}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    invoke-virtual {v4, v0}, Ljava/lang/StringBuilder;->append(I)Ljava/lang/StringBuilder;

    invoke-virtual {v4}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;

    move-result-object v4

    invoke-static {v2, v4}, Landroid/util/Log;->d(Ljava/lang/String;Ljava/lang/String;)I

    .line 145
    :cond_0
    invoke-static {}, Ljava/lang/Thread;->currentThread()Ljava/lang/Thread;

    move-result-object v2

    invoke-virtual {v2}, Ljava/lang/Thread;->getId()J

    move-result-wide v4

    invoke-static {v4, v5}, Ljava/lang/Long;->valueOf(J)Ljava/lang/Long;

    move-result-object v2

    .line 146
    .local v2, "threadId":Ljava/lang/Long;
    sget-object v4, Ledu/utsa/sefm/heapsnapshot/Snapshot;->isThreadCheckingObjectMap:Ljava/util/Map;

    invoke-interface {v4, v2}, Ljava/util/Map;->containsKey(Ljava/lang/Object;)Z

    move-result v4

    const/4 v10, 0x0

    if-nez v4, :cond_1

    .line 147
    sget-object v4, Ledu/utsa/sefm/heapsnapshot/Snapshot;->isThreadCheckingObjectMap:Ljava/util/Map;

    invoke-static {v10}, Ljava/lang/Boolean;->valueOf(Z)Ljava/lang/Boolean;

    move-result-object v5

    invoke-interface {v4, v2, v5}, Ljava/util/Map;->put(Ljava/lang/Object;Ljava/lang/Object;)Ljava/lang/Object;

    .line 149
    const-string v4, "Snap-Debug"

    new-instance v5, Ljava/lang/StringBuilder;

    invoke-direct {v5}, Ljava/lang/StringBuilder;-><init>()V

    const-string v6, "Creating entry in thread map, Thread ID is "

    invoke-virtual {v5, v6}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    invoke-virtual {v5, v2}, Ljava/lang/StringBuilder;->append(Ljava/lang/Object;)Ljava/lang/StringBuilder;

    invoke-virtual {v5}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;

    move-result-object v5

    invoke-static {v4, v5}, Landroid/util/Log;->e(Ljava/lang/String;Ljava/lang/String;)I

    .line 154
    :cond_1
    sget-object v4, Ledu/utsa/sefm/heapsnapshot/Snapshot;->isThreadCheckingObjectMap:Ljava/util/Map;

    invoke-interface {v4, v2}, Ljava/util/Map;->get(Ljava/lang/Object;)Ljava/lang/Object;

    move-result-object v4

    move-object v11, v4

    check-cast v11, Ljava/lang/Boolean;

    .line 163
    .local v11, "isCheckingObject":Ljava/lang/Boolean;
    invoke-virtual {v11}, Ljava/lang/Boolean;->booleanValue()Z

    move-result v4

    const/4 v5, -0x1

    if-eqz v4, :cond_2

    .line 164
    const-string v3, "Snap-Debug"

    new-instance v4, Ljava/lang/StringBuilder;

    invoke-direct {v4}, Ljava/lang/StringBuilder;-><init>()V

    const-string v6, "Avoided Infinite recursion at invocation: "

    invoke-virtual {v4, v6}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    invoke-virtual {v4, p1}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    invoke-virtual {v4}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;

    move-result-object v4

    invoke-static {v3, v4}, Landroid/util/Log;->d(Ljava/lang/String;Ljava/lang/String;)I

    .line 169
    const-string v3, "Snap-Debug"

    new-instance v4, Ljava/lang/StringBuilder;

    invoke-direct {v4}, Ljava/lang/StringBuilder;-><init>()V

    const-string v6, "Thread ID is "

    invoke-virtual {v4, v6}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    invoke-virtual {v4, v2}, Ljava/lang/StringBuilder;->append(Ljava/lang/Object;)Ljava/lang/StringBuilder;

    const-string v6, ", Printing stacktrace:"

    invoke-virtual {v4, v6}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    invoke-virtual {v4}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;

    move-result-object v4

    invoke-static {v3, v4}, Landroid/util/Log;->e(Ljava/lang/String;Ljava/lang/String;)I

    .line 170
    new-instance v3, Ljava/lang/Exception;

    const-string v4, "Snap-Debug"

    invoke-direct {v3, v4}, Ljava/lang/Exception;-><init>(Ljava/lang/String;)V

    invoke-virtual {v3}, Ljava/lang/Exception;->printStackTrace()V

    .line 173
    return v5

    .line 176
    :cond_2
    const/4 v12, 0x0

    .line 177
    .local v12, "currentInspectionDepth":I
    new-instance v7, Ljava/util/ArrayList;

    invoke-direct {v7}, Ljava/util/ArrayList;-><init>()V

    .line 179
    .local v7, "accessPath":Ljava/util/List;, "Ljava/util/List<Ledu/utsa/sefm/heapsnapshot/Snapshot$FieldInfo;>;"
    if-nez p0, :cond_3

    .line 180
    return v5

    .line 184
    :cond_3
    sget-object v4, Ledu/utsa/sefm/heapsnapshot/Snapshot;->isThreadCheckingObjectMap:Ljava/util/Map;

    invoke-static {v3}, Ljava/lang/Boolean;->valueOf(Z)Ljava/lang/Boolean;

    move-result-object v3

    invoke-interface {v4, v2, v3}, Ljava/util/Map;->put(Ljava/lang/Object;Ljava/lang/Object;)Ljava/lang/Object;

    .line 191
    const-string v5, "."

    move-object v4, p0

    move v6, v12

    move-object v8, p1

    move v9, v0

    invoke-static/range {v4 .. v9}, Ledu/utsa/sefm/heapsnapshot/Snapshot;->checkObjectForPIIRecursive(Ljava/lang/Object;Ljava/lang/String;ILjava/util/List;Ljava/lang/String;I)I

    move-result v3

    .line 194
    .local v3, "result":I
    sget-object v4, Ledu/utsa/sefm/heapsnapshot/Snapshot;->isThreadCheckingObjectMap:Ljava/util/Map;

    invoke-static {v10}, Ljava/lang/Boolean;->valueOf(Z)Ljava/lang/Boolean;

    move-result-object v5

    invoke-interface {v4, v2, v5}, Ljava/util/Map;->put(Ljava/lang/Object;Ljava/lang/Object;)Ljava/lang/Object;

    .line 200
    return v3

    .line 132
    .end local v1    # "div":I
    .end local v2    # "threadId":Ljava/lang/Long;
    .end local v3    # "result":I
    .end local v7    # "accessPath":Ljava/util/List;, "Ljava/util/List<Ledu/utsa/sefm/heapsnapshot/Snapshot$FieldInfo;>;"
    .end local v11    # "isCheckingObject":Ljava/lang/Boolean;
    .end local v12    # "currentInspectionDepth":I
    :catchall_0
    move-exception v2

    :try_start_1
    monitor-exit v1
    :try_end_1
    .catchall {:try_start_1 .. :try_end_1} :catchall_0

    throw v2
.end method

.method private static checkObjectForPIIRecursive(Ljava/lang/Object;Ljava/lang/String;ILjava/util/List;Ljava/lang/String;I)I
    .locals 22
    .param p0, "instance"    # Ljava/lang/Object;
    .param p1, "instanceName"    # Ljava/lang/String;
    .param p2, "curDepth"    # I
    .param p4, "invocationDescription"    # Ljava/lang/String;
    .param p5, "localCallID"    # I
    .annotation system Ldalvik/annotation/Signature;
        value = {
            "(",
            "Ljava/lang/Object;",
            "Ljava/lang/String;",
            "I",
            "Ljava/util/List<",
            "Ledu/utsa/sefm/heapsnapshot/Snapshot$FieldInfo;",
            ">;",
            "Ljava/lang/String;",
            "I)I"
        }
    .end annotation

    .line 212
    .local p3, "accessPath":Ljava/util/List;, "Ljava/util/List<Ledu/utsa/sefm/heapsnapshot/Snapshot$FieldInfo;>;"
    move-object/from16 v1, p0

    move/from16 v2, p2

    move-object/from16 v9, p3

    move-object/from16 v10, p4

    const/4 v11, -0x1

    if-nez v1, :cond_0

    .line 213
    return v11

    .line 215
    :cond_0
    invoke-virtual/range {p0 .. p0}, Ljava/lang/Object;->getClass()Ljava/lang/Class;

    move-result-object v12

    .line 216
    .local v12, "objClass":Ljava/lang/Class;, "Ljava/lang/Class<*>;"
    new-instance v0, Ledu/utsa/sefm/heapsnapshot/Snapshot$FieldInfo;

    invoke-virtual {v12}, Ljava/lang/Class;->getName()Ljava/lang/String;

    move-result-object v3

    move-object/from16 v13, p1

    invoke-direct {v0, v3, v13}, Ledu/utsa/sefm/heapsnapshot/Snapshot$FieldInfo;-><init>(Ljava/lang/String;Ljava/lang/String;)V

    invoke-interface {v9, v0}, Ljava/util/List;->add(Ljava/lang/Object;)Z

    .line 217
    const/4 v0, 0x0

    .line 224
    .local v0, "childFoundLeak":Z
    const-class v3, Ljava/lang/String;

    invoke-virtual {v12, v3}, Ljava/lang/Object;->equals(Ljava/lang/Object;)Z

    move-result v3

    const-string v14, "Snapshot"

    if-eqz v3, :cond_3

    .line 226
    move-object v3, v1

    check-cast v3, Ljava/lang/String;

    .line 229
    .local v3, "stringInstance":Ljava/lang/String;
    sget-object v4, Ledu/utsa/sefm/heapsnapshot/Snapshot;->PII:Ljava/util/List;

    invoke-interface {v4}, Ljava/util/List;->iterator()Ljava/util/Iterator;

    move-result-object v4

    :goto_0
    invoke-interface {v4}, Ljava/util/Iterator;->hasNext()Z

    move-result v5

    const-string v6, ";"

    if-eqz v5, :cond_2

    invoke-interface {v4}, Ljava/util/Iterator;->next()Ljava/lang/Object;

    move-result-object v5

    check-cast v5, Ljava/lang/String;

    .line 230
    .local v5, "piiString":Ljava/lang/String;
    invoke-virtual {v3, v5}, Ljava/lang/String;->contains(Ljava/lang/CharSequence;)Z

    move-result v7

    if-eqz v7, :cond_1

    .line 232
    new-instance v7, Ljava/lang/StringBuilder;

    invoke-direct {v7}, Ljava/lang/StringBuilder;-><init>()V

    invoke-virtual {v7, v10}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    invoke-virtual {v7, v6}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    invoke-virtual {v7, v9}, Ljava/lang/StringBuilder;->append(Ljava/lang/Object;)Ljava/lang/StringBuilder;

    invoke-virtual {v7, v6}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    invoke-virtual {v7, v3}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    invoke-virtual {v7}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;

    move-result-object v6

    invoke-static {v14, v6}, Landroid/util/Log;->d(Ljava/lang/String;Ljava/lang/String;)I

    .line 233
    const/4 v0, 0x1

    .line 235
    .end local v5    # "piiString":Ljava/lang/String;
    :cond_1
    goto :goto_0

    .line 238
    :cond_2
    const-string v4, "\\*\\*\\*\\d{12}\\*\\*\\*"

    invoke-static {v4}, Ljava/util/regex/Pattern;->compile(Ljava/lang/String;)Ljava/util/regex/Pattern;

    move-result-object v4

    .line 239
    .local v4, "pattern":Ljava/util/regex/Pattern;
    invoke-virtual {v4, v3}, Ljava/util/regex/Pattern;->matcher(Ljava/lang/CharSequence;)Ljava/util/regex/Matcher;

    move-result-object v5

    invoke-virtual {v5}, Ljava/util/regex/Matcher;->find()Z

    move-result v5

    if-eqz v5, :cond_3

    .line 241
    new-instance v5, Ljava/lang/StringBuilder;

    invoke-direct {v5}, Ljava/lang/StringBuilder;-><init>()V

    invoke-virtual {v5, v10}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    invoke-virtual {v5, v6}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    invoke-virtual {v5, v9}, Ljava/lang/StringBuilder;->append(Ljava/lang/Object;)Ljava/lang/StringBuilder;

    invoke-virtual {v5, v6}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    invoke-virtual {v5, v3}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    invoke-virtual {v5}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;

    move-result-object v5

    invoke-static {v14, v5}, Landroid/util/Log;->d(Ljava/lang/String;Ljava/lang/String;)I

    .line 242
    const/4 v0, 0x1

    .line 248
    .end local v3    # "stringInstance":Ljava/lang/String;
    .end local v4    # "pattern":Ljava/util/regex/Pattern;
    :cond_3
    const/4 v15, 0x1

    if-lt v2, v15, :cond_5

    .line 249
    invoke-interface/range {p3 .. p3}, Ljava/util/List;->size()I

    move-result v3

    sub-int/2addr v3, v15

    invoke-interface {v9, v3}, Ljava/util/List;->remove(I)Ljava/lang/Object;

    .line 250
    if-eqz v0, :cond_4

    .line 251
    return p5

    .line 254
    :cond_4
    return v11

    .line 260
    :cond_5
    invoke-virtual {v12}, Ljava/lang/Class;->getDeclaredFields()[Ljava/lang/reflect/Field;

    move-result-object v8

    .line 261
    .local v8, "fields":[Ljava/lang/reflect/Field;
    array-length v7, v8

    const/16 v16, 0x0

    move/from16 v17, v0

    const/4 v6, 0x0

    .end local v0    # "childFoundLeak":Z
    .local v17, "childFoundLeak":Z
    :goto_1
    if-ge v6, v7, :cond_f

    aget-object v5, v8, v6

    .line 264
    .local v5, "field":Ljava/lang/reflect/Field;
    const/4 v3, 0x0

    .line 267
    .local v3, "canAccess":Z
    :try_start_0
    invoke-virtual {v5, v15}, Ljava/lang/reflect/Field;->setAccessible(Z)V
    :try_end_0
    .catch Ljava/lang/SecurityException; {:try_start_0 .. :try_end_0} :catch_0

    .line 268
    const/4 v3, 0x1

    .line 282
    move/from16 v18, v3

    goto :goto_2

    .line 270
    :catch_0
    move-exception v0

    move-object v4, v0

    move-object v0, v4

    .line 273
    .local v0, "e":Ljava/lang/SecurityException;
    const-string v4, "opens ([\\w.]+)"

    const/4 v11, 0x2

    invoke-static {v4, v11}, Ljava/util/regex/Pattern;->compile(Ljava/lang/String;I)Ljava/util/regex/Pattern;

    move-result-object v4

    .line 274
    .restart local v4    # "pattern":Ljava/util/regex/Pattern;
    invoke-virtual {v0}, Ljava/lang/SecurityException;->getMessage()Ljava/lang/String;

    move-result-object v11

    invoke-virtual {v4, v11}, Ljava/util/regex/Pattern;->matcher(Ljava/lang/CharSequence;)Ljava/util/regex/Matcher;

    move-result-object v11

    .line 275
    .local v11, "matcher":Ljava/util/regex/Matcher;
    invoke-virtual {v11}, Ljava/util/regex/Matcher;->find()Z

    move-result v19

    if-eqz v19, :cond_6

    .line 276
    invoke-virtual {v11, v15}, Ljava/util/regex/Matcher;->group(I)Ljava/lang/String;

    move-result-object v19

    .line 277
    .local v19, "closedPackageName":Ljava/lang/String;
    const/4 v15, 0x2

    new-array v15, v15, [Ljava/lang/Object;

    aput-object v19, v15, v16

    const/16 v18, 0x1

    aput-object v5, v15, v18

    move/from16 v18, v3

    .end local v3    # "canAccess":Z
    .local v18, "canAccess":Z
    const-string v3, "Closed Package %s in Field %s"

    invoke-static {v3, v15}, Ljava/lang/String;->format(Ljava/lang/String;[Ljava/lang/Object;)Ljava/lang/String;

    move-result-object v3

    invoke-static {v14, v3}, Landroid/util/Log;->d(Ljava/lang/String;Ljava/lang/String;)I

    .line 278
    .end local v19    # "closedPackageName":Ljava/lang/String;
    goto :goto_2

    .line 280
    .end local v18    # "canAccess":Z
    .restart local v3    # "canAccess":Z
    :cond_6
    move/from16 v18, v3

    .end local v3    # "canAccess":Z
    .restart local v18    # "canAccess":Z
    new-instance v3, Ljava/lang/StringBuilder;

    invoke-direct {v3}, Ljava/lang/StringBuilder;-><init>()V

    const-string v15, "Some unrecognized Closed Package! "

    invoke-virtual {v3, v15}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    invoke-virtual {v0}, Ljava/lang/SecurityException;->getMessage()Ljava/lang/String;

    move-result-object v15

    invoke-virtual {v3, v15}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    invoke-virtual {v3}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;

    move-result-object v3

    invoke-static {v14, v3}, Landroid/util/Log;->d(Ljava/lang/String;Ljava/lang/String;)I

    .line 284
    .end local v0    # "e":Ljava/lang/SecurityException;
    .end local v4    # "pattern":Ljava/util/regex/Pattern;
    .end local v11    # "matcher":Ljava/util/regex/Matcher;
    :goto_2
    if-eqz v18, :cond_e

    .line 286
    const/4 v0, 0x0

    .line 287
    .local v0, "fieldInstance":Ljava/lang/Object;
    :try_start_1
    invoke-virtual {v5}, Ljava/lang/reflect/Field;->getModifiers()I

    move-result v3

    invoke-static {v3}, Ljava/lang/reflect/Modifier;->isStatic(I)Z

    move-result v3
    :try_end_1
    .catch Ljava/lang/IllegalAccessException; {:try_start_1 .. :try_end_1} :catch_3

    if-eqz v3, :cond_7

    .line 288
    const/4 v3, 0x0

    :try_start_2
    invoke-virtual {v5, v3}, Ljava/lang/reflect/Field;->get(Ljava/lang/Object;)Ljava/lang/Object;

    move-result-object v3
    :try_end_2
    .catch Ljava/lang/IllegalAccessException; {:try_start_2 .. :try_end_2} :catch_1

    move-object v0, v3

    goto :goto_3

    .line 360
    .end local v0    # "fieldInstance":Ljava/lang/Object;
    :catch_1
    move-exception v0

    move-object/from16 v19, v5

    move-object/from16 v21, v8

    goto/16 :goto_4

    .line 291
    .restart local v0    # "fieldInstance":Ljava/lang/Object;
    :cond_7
    :try_start_3
    invoke-virtual {v5, v1}, Ljava/lang/reflect/Field;->get(Ljava/lang/Object;)Ljava/lang/Object;

    move-result-object v3

    move-object v0, v3

    .line 294
    :goto_3
    if-nez v0, :cond_8

    .line 295
    move v15, v6

    move/from16 v20, v7

    move-object/from16 v21, v8

    goto/16 :goto_5

    .line 298
    :cond_8
    invoke-virtual {v0}, Ljava/lang/Object;->getClass()Ljava/lang/Class;

    move-result-object v3

    move-object v11, v3

    .line 306
    .local v11, "fieldClass":Ljava/lang/Class;, "Ljava/lang/Class<*>;"
    invoke-virtual {v11}, Ljava/lang/Class;->isPrimitive()Z

    move-result v3

    if-eqz v3, :cond_9

    .line 308
    move v15, v6

    move/from16 v20, v7

    move-object/from16 v21, v8

    goto/16 :goto_5

    .line 310
    :cond_9
    sget-object v3, Ledu/utsa/sefm/heapsnapshot/Snapshot;->EXCLUDED_CLASSES:Ljava/util/List;

    invoke-interface {v3, v11}, Ljava/util/List;->contains(Ljava/lang/Object;)Z

    move-result v3

    if-eqz v3, :cond_a

    .line 312
    move v15, v6

    move/from16 v20, v7

    move-object/from16 v21, v8

    goto :goto_5

    .line 314
    :cond_a
    const-class v3, Ljava/util/Collection;

    invoke-virtual {v3, v11}, Ljava/lang/Class;->isAssignableFrom(Ljava/lang/Class;)Z

    move-result v3

    if-eqz v3, :cond_b

    .line 328
    move v15, v6

    move/from16 v20, v7

    move-object/from16 v21, v8

    goto :goto_5

    .line 331
    :cond_b
    const-class v3, Ljava/util/Map;

    invoke-virtual {v3, v11}, Ljava/lang/Class;->isAssignableFrom(Ljava/lang/Class;)Z

    move-result v3

    if-eqz v3, :cond_c

    .line 350
    move v15, v6

    move/from16 v20, v7

    move-object/from16 v21, v8

    goto :goto_5

    .line 355
    :cond_c
    invoke-virtual {v5}, Ljava/lang/reflect/Field;->getName()Ljava/lang/String;

    move-result-object v4
    :try_end_3
    .catch Ljava/lang/IllegalAccessException; {:try_start_3 .. :try_end_3} :catch_3

    add-int/lit8 v15, v2, 0x1

    move-object v3, v0

    move-object/from16 v19, v5

    .end local v5    # "field":Ljava/lang/reflect/Field;
    .local v19, "field":Ljava/lang/reflect/Field;
    move v5, v15

    move v15, v6

    move-object/from16 v6, p3

    move/from16 v20, v7

    move-object/from16 v7, p4

    move-object/from16 v21, v8

    .end local v8    # "fields":[Ljava/lang/reflect/Field;
    .local v21, "fields":[Ljava/lang/reflect/Field;
    move/from16 v8, p5

    :try_start_4
    invoke-static/range {v3 .. v8}, Ledu/utsa/sefm/heapsnapshot/Snapshot;->checkObjectForPIIRecursive(Ljava/lang/Object;Ljava/lang/String;ILjava/util/List;Ljava/lang/String;I)I

    move-result v3
    :try_end_4
    .catch Ljava/lang/IllegalAccessException; {:try_start_4 .. :try_end_4} :catch_2

    .line 356
    .local v3, "result":I
    const/4 v4, -0x1

    if-eq v3, v4, :cond_d

    .line 357
    const/16 v17, 0x1

    .line 362
    .end local v0    # "fieldInstance":Ljava/lang/Object;
    .end local v3    # "result":I
    .end local v11    # "fieldClass":Ljava/lang/Class;, "Ljava/lang/Class<*>;"
    :cond_d
    goto :goto_5

    .line 360
    :catch_2
    move-exception v0

    goto :goto_4

    .end local v19    # "field":Ljava/lang/reflect/Field;
    .end local v21    # "fields":[Ljava/lang/reflect/Field;
    .restart local v5    # "field":Ljava/lang/reflect/Field;
    .restart local v8    # "fields":[Ljava/lang/reflect/Field;
    :catch_3
    move-exception v0

    move-object/from16 v19, v5

    move-object/from16 v21, v8

    .line 361
    .end local v5    # "field":Ljava/lang/reflect/Field;
    .end local v8    # "fields":[Ljava/lang/reflect/Field;
    .local v0, "e":Ljava/lang/IllegalAccessException;
    .restart local v19    # "field":Ljava/lang/reflect/Field;
    .restart local v21    # "fields":[Ljava/lang/reflect/Field;
    :goto_4
    new-instance v3, Ljava/lang/RuntimeException;

    invoke-direct {v3, v0}, Ljava/lang/RuntimeException;-><init>(Ljava/lang/Throwable;)V

    throw v3

    .line 284
    .end local v0    # "e":Ljava/lang/IllegalAccessException;
    .end local v19    # "field":Ljava/lang/reflect/Field;
    .end local v21    # "fields":[Ljava/lang/reflect/Field;
    .restart local v5    # "field":Ljava/lang/reflect/Field;
    .restart local v8    # "fields":[Ljava/lang/reflect/Field;
    :cond_e
    move-object/from16 v19, v5

    move v15, v6

    move/from16 v20, v7

    move-object/from16 v21, v8

    .line 261
    .end local v5    # "field":Ljava/lang/reflect/Field;
    .end local v8    # "fields":[Ljava/lang/reflect/Field;
    .end local v18    # "canAccess":Z
    .restart local v21    # "fields":[Ljava/lang/reflect/Field;
    :goto_5
    add-int/lit8 v6, v15, 0x1

    move/from16 v7, v20

    move-object/from16 v8, v21

    const/4 v11, -0x1

    const/4 v15, 0x1

    goto/16 :goto_1

    .line 367
    .end local v21    # "fields":[Ljava/lang/reflect/Field;
    .restart local v8    # "fields":[Ljava/lang/reflect/Field;
    :cond_f
    move-object/from16 v21, v8

    .end local v8    # "fields":[Ljava/lang/reflect/Field;
    .restart local v21    # "fields":[Ljava/lang/reflect/Field;
    invoke-interface/range {p3 .. p3}, Ljava/util/List;->size()I

    move-result v0

    const/4 v3, 0x1

    sub-int/2addr v0, v3

    invoke-interface {v9, v0}, Ljava/util/List;->remove(I)Ljava/lang/Object;

    .line 368
    if-eqz v17, :cond_10

    .line 369
    return p5

    .line 372
    :cond_10
    const/4 v3, -0x1

    return v3
.end method

.method public static largeLog(Ljava/lang/String;Ljava/lang/String;)V
    .locals 2
    .param p0, "tag"    # Ljava/lang/String;
    .param p1, "content"    # Ljava/lang/String;

    .line 407
    invoke-virtual {p1}, Ljava/lang/String;->length()I

    move-result v0

    const/16 v1, 0xfa0

    if-le v0, v1, :cond_0

    .line 408
    const/4 v0, 0x0

    invoke-virtual {p1, v0, v1}, Ljava/lang/String;->substring(II)Ljava/lang/String;

    move-result-object v0

    invoke-static {p0, v0}, Landroid/util/Log;->d(Ljava/lang/String;Ljava/lang/String;)I

    .line 409
    invoke-virtual {p1, v1}, Ljava/lang/String;->substring(I)Ljava/lang/String;

    move-result-object v0

    invoke-static {p0, v0}, Ledu/utsa/sefm/heapsnapshot/Snapshot;->largeLog(Ljava/lang/String;Ljava/lang/String;)V

    goto :goto_0

    .line 411
    :cond_0
    invoke-static {p0, p1}, Landroid/util/Log;->d(Ljava/lang/String;Ljava/lang/String;)I

    .line 413
    :goto_0
    return-void
.end method

.method public static logHarnessedSource(Ljava/lang/Object;Ljava/lang/String;)V
    .locals 5
    .param p0, "original_return_value"    # Ljava/lang/Object;
    .param p1, "message"    # Ljava/lang/String;

    .line 377
    const-string v0, "HarnessedSource"

    .line 378
    .local v0, "HARNESSED_SOURCE_TAG":Ljava/lang/String;
    invoke-virtual {p0}, Ljava/lang/Object;->getClass()Ljava/lang/Class;

    move-result-object v1

    .line 379
    .local v1, "objClass":Ljava/lang/Class;, "Ljava/lang/Class<*>;"
    const-class v2, Ljava/lang/String;

    invoke-virtual {v1, v2}, Ljava/lang/Object;->equals(Ljava/lang/Object;)Z

    move-result v2

    const-string v3, ";"

    if-eqz v2, :cond_0

    .line 380
    move-object v2, p0

    check-cast v2, Ljava/lang/String;

    .line 382
    .local v2, "original_return_value_cast":Ljava/lang/String;
    new-instance v4, Ljava/lang/StringBuilder;

    invoke-direct {v4}, Ljava/lang/StringBuilder;-><init>()V

    invoke-virtual {v4, p1}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    invoke-virtual {v4, v3}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    invoke-virtual {v4, v2}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    invoke-virtual {v4}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;

    move-result-object v3

    invoke-static {v0, v3}, Landroid/util/Log;->d(Ljava/lang/String;Ljava/lang/String;)I

    .line 383
    .end local v2    # "original_return_value_cast":Ljava/lang/String;
    goto :goto_0

    .line 385
    :cond_0
    new-instance v2, Ljava/lang/StringBuilder;

    invoke-direct {v2}, Ljava/lang/StringBuilder;-><init>()V

    invoke-virtual {v2, p1}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    invoke-virtual {v2, v3}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    invoke-virtual {v2}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;

    move-result-object v2

    invoke-static {v0, v2}, Landroid/util/Log;->d(Ljava/lang/String;Ljava/lang/String;)I

    .line 388
    :goto_0
    return-void
.end method

.method public static takeSnapshot(Ljava/lang/Object;I)Lorg/json/JSONObject;
    .locals 12
    .param p0, "obj"    # Ljava/lang/Object;
    .param p1, "inspectionDepth"    # I
    .annotation system Ldalvik/annotation/Throws;
        value = {
            Lorg/json/JSONException;
        }
    .end annotation

    .line 45
    new-instance v0, Lorg/json/JSONObject;

    invoke-direct {v0}, Lorg/json/JSONObject;-><init>()V

    .line 47
    .local v0, "resultJson":Lorg/json/JSONObject;
    invoke-virtual {p0}, Ljava/lang/Object;->getClass()Ljava/lang/Class;

    move-result-object v1

    .line 48
    .local v1, "objClass":Ljava/lang/Class;, "Ljava/lang/Class<*>;"
    invoke-virtual {v1}, Ljava/lang/Class;->getName()Ljava/lang/String;

    move-result-object v2

    const-string v3, "class_name"

    invoke-virtual {v0, v3, v2}, Lorg/json/JSONObject;->put(Ljava/lang/String;Ljava/lang/Object;)Lorg/json/JSONObject;

    .line 49
    invoke-virtual {v1}, Ljava/lang/Class;->getModifiers()I

    move-result v2

    const-string v3, "modifiers"

    invoke-virtual {v0, v3, v2}, Lorg/json/JSONObject;->put(Ljava/lang/String;I)Lorg/json/JSONObject;

    .line 51
    invoke-virtual {p0}, Ljava/lang/Object;->hashCode()I

    move-result v2

    const-string v3, "hash_code"

    invoke-virtual {v0, v3, v2}, Lorg/json/JSONObject;->put(Ljava/lang/String;I)Lorg/json/JSONObject;

    .line 54
    invoke-virtual {v1}, Ljava/lang/Class;->getDeclaredFields()[Ljava/lang/reflect/Field;

    move-result-object v2

    .line 59
    .local v2, "fields":[Ljava/lang/reflect/Field;
    array-length v3, v2

    const/4 v4, 0x0

    :goto_0
    if-ge v4, v3, :cond_4

    aget-object v5, v2, v4

    .line 60
    .local v5, "field":Ljava/lang/reflect/Field;
    invoke-virtual {v5}, Ljava/lang/reflect/Field;->getName()Ljava/lang/String;

    move-result-object v6

    .line 64
    .local v6, "fieldName":Ljava/lang/String;
    const/4 v7, 0x1

    invoke-virtual {v5, v7}, Ljava/lang/reflect/Field;->setAccessible(Z)V

    .line 87
    const/4 v8, 0x1

    .line 88
    .local v8, "canAccess":Z
    if-eqz v8, :cond_3

    .line 91
    const/4 v9, 0x0

    .line 92
    .local v9, "child":Ljava/lang/Object;
    :try_start_0
    invoke-virtual {v5}, Ljava/lang/reflect/Field;->getModifiers()I

    move-result v10

    invoke-static {v10}, Ljava/lang/reflect/Modifier;->isStatic(I)Z

    move-result v10

    const/4 v11, 0x0

    if-eqz v10, :cond_0

    .line 93
    invoke-virtual {v5, v11}, Ljava/lang/reflect/Field;->get(Ljava/lang/Object;)Ljava/lang/Object;

    move-result-object v10

    move-object v9, v10

    goto :goto_1

    .line 96
    :cond_0
    invoke-virtual {v5, p0}, Ljava/lang/reflect/Field;->get(Ljava/lang/Object;)Ljava/lang/Object;

    move-result-object v10

    move-object v9, v10

    .line 100
    :goto_1
    if-nez v9, :cond_1

    .line 101
    move-object v7, v11

    check-cast v7, Ljava/util/Map;

    invoke-virtual {v0, v6, v11}, Lorg/json/JSONObject;->put(Ljava/lang/String;Ljava/lang/Object;)Lorg/json/JSONObject;

    goto :goto_2

    .line 104
    :cond_1
    if-le p1, v7, :cond_2

    .line 105
    add-int/lit8 v7, p1, -0x1

    invoke-static {v9, v7}, Ledu/utsa/sefm/heapsnapshot/Snapshot;->takeSnapshot(Ljava/lang/Object;I)Lorg/json/JSONObject;

    move-result-object v7

    invoke-virtual {v0, v6, v7}, Lorg/json/JSONObject;->put(Ljava/lang/String;Ljava/lang/Object;)Lorg/json/JSONObject;

    goto :goto_2

    .line 108
    :cond_2
    const-string v7, "*"

    invoke-virtual {v0, v6, v7}, Lorg/json/JSONObject;->put(Ljava/lang/String;Ljava/lang/Object;)Lorg/json/JSONObject;
    :try_end_0
    .catch Ljava/lang/IllegalAccessException; {:try_start_0 .. :try_end_0} :catch_0

    .line 113
    .end local v9    # "child":Ljava/lang/Object;
    :goto_2
    goto :goto_3

    .line 111
    :catch_0
    move-exception v3

    .line 112
    .local v3, "e":Ljava/lang/IllegalAccessException;
    new-instance v4, Ljava/lang/RuntimeException;

    invoke-direct {v4, v3}, Ljava/lang/RuntimeException;-><init>(Ljava/lang/Throwable;)V

    throw v4

    .line 59
    .end local v3    # "e":Ljava/lang/IllegalAccessException;
    .end local v5    # "field":Ljava/lang/reflect/Field;
    .end local v6    # "fieldName":Ljava/lang/String;
    .end local v8    # "canAccess":Z
    :cond_3
    :goto_3
    add-int/lit8 v4, v4, 0x1

    goto :goto_0

    .line 117
    :cond_4
    return-object v0
.end method
