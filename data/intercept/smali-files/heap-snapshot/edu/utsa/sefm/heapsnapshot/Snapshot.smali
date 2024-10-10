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

    .line 28
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

    .line 29
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

    .line 33
    sput v2, Ledu/utsa/sefm/heapsnapshot/Snapshot;->callId:I

    .line 35
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

    .line 121
    const/4 v0, 0x0

    .line 122
    .local v0, "localCallId":I
    const-class v1, Ledu/utsa/sefm/heapsnapshot/Snapshot;

    monitor-enter v1

    .line 123
    :try_start_0
    sget v2, Ledu/utsa/sefm/heapsnapshot/Snapshot;->callId:I

    const/4 v3, 0x1

    add-int/2addr v2, v3

    sput v2, Ledu/utsa/sefm/heapsnapshot/Snapshot;->callId:I

    .line 124
    move v0, v2

    .line 125
    monitor-exit v1
    :try_end_0
    .catchall {:try_start_0 .. :try_end_0} :catchall_0

    .line 129
    const/16 v1, 0x64

    .line 130
    .local v1, "div":I
    rem-int v2, v0, v1

    if-nez v2, :cond_0

    .line 131
    const-string v2, "Snap-Debug"

    new-instance v4, Ljava/lang/StringBuilder;

    invoke-direct {v4}, Ljava/lang/StringBuilder;-><init>()V

    const-string v5, "Calls to checkObjectForPII :"

    invoke-virtual {v4, v5}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    invoke-virtual {v4, v0}, Ljava/lang/StringBuilder;->append(I)Ljava/lang/StringBuilder;

    invoke-virtual {v4}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;

    move-result-object v4

    invoke-static {v2, v4}, Landroid/util/Log;->d(Ljava/lang/String;Ljava/lang/String;)I

    .line 138
    :cond_0
    invoke-static {}, Ljava/lang/Thread;->currentThread()Ljava/lang/Thread;

    move-result-object v2

    invoke-virtual {v2}, Ljava/lang/Thread;->getId()J

    move-result-wide v4

    invoke-static {v4, v5}, Ljava/lang/Long;->valueOf(J)Ljava/lang/Long;

    move-result-object v2

    .line 139
    .local v2, "threadId":Ljava/lang/Long;
    sget-object v4, Ledu/utsa/sefm/heapsnapshot/Snapshot;->isThreadCheckingObjectMap:Ljava/util/Map;

    invoke-interface {v4, v2}, Ljava/util/Map;->containsKey(Ljava/lang/Object;)Z

    move-result v4

    const/4 v10, 0x0

    if-nez v4, :cond_1

    .line 140
    sget-object v4, Ledu/utsa/sefm/heapsnapshot/Snapshot;->isThreadCheckingObjectMap:Ljava/util/Map;

    invoke-static {v10}, Ljava/lang/Boolean;->valueOf(Z)Ljava/lang/Boolean;

    move-result-object v5

    invoke-interface {v4, v2, v5}, Ljava/util/Map;->put(Ljava/lang/Object;Ljava/lang/Object;)Ljava/lang/Object;

    .line 142
    const-string v4, "Snap-Debug"

    new-instance v5, Ljava/lang/StringBuilder;

    invoke-direct {v5}, Ljava/lang/StringBuilder;-><init>()V

    const-string v6, "Creating entry in thread map, Thread ID is "

    invoke-virtual {v5, v6}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    invoke-virtual {v5, v2}, Ljava/lang/StringBuilder;->append(Ljava/lang/Object;)Ljava/lang/StringBuilder;

    invoke-virtual {v5}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;

    move-result-object v5

    invoke-static {v4, v5}, Landroid/util/Log;->e(Ljava/lang/String;Ljava/lang/String;)I

    .line 147
    :cond_1
    sget-object v4, Ledu/utsa/sefm/heapsnapshot/Snapshot;->isThreadCheckingObjectMap:Ljava/util/Map;

    invoke-interface {v4, v2}, Ljava/util/Map;->get(Ljava/lang/Object;)Ljava/lang/Object;

    move-result-object v4

    move-object v11, v4

    check-cast v11, Ljava/lang/Boolean;

    .line 156
    .local v11, "isCheckingObject":Ljava/lang/Boolean;
    invoke-virtual {v11}, Ljava/lang/Boolean;->booleanValue()Z

    move-result v4

    const/4 v5, -0x1

    if-eqz v4, :cond_2

    .line 157
    const-string v3, "Snap-Debug"

    new-instance v4, Ljava/lang/StringBuilder;

    invoke-direct {v4}, Ljava/lang/StringBuilder;-><init>()V

    const-string v6, "Avoided Infinite recursion at invocation: "

    invoke-virtual {v4, v6}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    invoke-virtual {v4, p1}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    invoke-virtual {v4}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;

    move-result-object v4

    invoke-static {v3, v4}, Landroid/util/Log;->d(Ljava/lang/String;Ljava/lang/String;)I

    .line 162
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

    .line 163
    new-instance v3, Ljava/lang/Exception;

    const-string v4, "Snap-Debug"

    invoke-direct {v3, v4}, Ljava/lang/Exception;-><init>(Ljava/lang/String;)V

    invoke-virtual {v3}, Ljava/lang/Exception;->printStackTrace()V

    .line 166
    return v5

    .line 169
    :cond_2
    const/4 v12, 0x0

    .line 170
    .local v12, "currentInspectionDepth":I
    new-instance v7, Ljava/util/ArrayList;

    invoke-direct {v7}, Ljava/util/ArrayList;-><init>()V

    .line 172
    .local v7, "accessPath":Ljava/util/List;, "Ljava/util/List<Ledu/utsa/sefm/heapsnapshot/Snapshot$FieldInfo;>;"
    if-nez p0, :cond_3

    .line 173
    return v5

    .line 177
    :cond_3
    sget-object v4, Ledu/utsa/sefm/heapsnapshot/Snapshot;->isThreadCheckingObjectMap:Ljava/util/Map;

    invoke-static {v3}, Ljava/lang/Boolean;->valueOf(Z)Ljava/lang/Boolean;

    move-result-object v3

    invoke-interface {v4, v2, v3}, Ljava/util/Map;->put(Ljava/lang/Object;Ljava/lang/Object;)Ljava/lang/Object;

    .line 184
    const-string v5, "."

    move-object v4, p0

    move v6, v12

    move-object v8, p1

    move v9, v0

    invoke-static/range {v4 .. v9}, Ledu/utsa/sefm/heapsnapshot/Snapshot;->checkObjectForPIIRecursive(Ljava/lang/Object;Ljava/lang/String;ILjava/util/List;Ljava/lang/String;I)I

    move-result v3

    .line 187
    .local v3, "result":I
    sget-object v4, Ledu/utsa/sefm/heapsnapshot/Snapshot;->isThreadCheckingObjectMap:Ljava/util/Map;

    invoke-static {v10}, Ljava/lang/Boolean;->valueOf(Z)Ljava/lang/Boolean;

    move-result-object v5

    invoke-interface {v4, v2, v5}, Ljava/util/Map;->put(Ljava/lang/Object;Ljava/lang/Object;)Ljava/lang/Object;

    .line 193
    return v3

    .line 125
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
    .locals 23
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

    .line 205
    .local p3, "accessPath":Ljava/util/List;, "Ljava/util/List<Ledu/utsa/sefm/heapsnapshot/Snapshot$FieldInfo;>;"
    move-object/from16 v1, p0

    move/from16 v2, p2

    move-object/from16 v9, p3

    const/4 v10, -0x1

    if-nez v1, :cond_0

    .line 206
    return v10

    .line 208
    :cond_0
    invoke-virtual/range {p0 .. p0}, Ljava/lang/Object;->getClass()Ljava/lang/Class;

    move-result-object v11

    .line 209
    .local v11, "objClass":Ljava/lang/Class;, "Ljava/lang/Class<*>;"
    new-instance v0, Ledu/utsa/sefm/heapsnapshot/Snapshot$FieldInfo;

    invoke-virtual {v11}, Ljava/lang/Class;->getName()Ljava/lang/String;

    move-result-object v3

    move-object/from16 v12, p1

    invoke-direct {v0, v3, v12}, Ledu/utsa/sefm/heapsnapshot/Snapshot$FieldInfo;-><init>(Ljava/lang/String;Ljava/lang/String;)V

    invoke-interface {v9, v0}, Ljava/util/List;->add(Ljava/lang/Object;)Z

    .line 210
    const/4 v0, 0x0

    .line 217
    .local v0, "childFoundLeak":Z
    const-class v3, Ljava/lang/String;

    invoke-virtual {v11, v3}, Ljava/lang/Object;->equals(Ljava/lang/Object;)Z

    move-result v3

    const-string v13, "Snapshot"

    if-eqz v3, :cond_3

    .line 219
    move-object v3, v1

    check-cast v3, Ljava/lang/String;

    .line 221
    .local v3, "stringInstance":Ljava/lang/String;
    sget-object v4, Ledu/utsa/sefm/heapsnapshot/Snapshot;->PII:Ljava/util/List;

    invoke-interface {v4}, Ljava/util/List;->iterator()Ljava/util/Iterator;

    move-result-object v4

    :goto_0
    invoke-interface {v4}, Ljava/util/Iterator;->hasNext()Z

    move-result v5

    if-eqz v5, :cond_2

    invoke-interface {v4}, Ljava/util/Iterator;->next()Ljava/lang/Object;

    move-result-object v5

    check-cast v5, Ljava/lang/String;

    .line 222
    .local v5, "piiString":Ljava/lang/String;
    invoke-virtual {v3, v5}, Ljava/lang/String;->contains(Ljava/lang/CharSequence;)Z

    move-result v6

    if-eqz v6, :cond_1

    .line 224
    new-instance v6, Ljava/lang/StringBuilder;

    invoke-direct {v6}, Ljava/lang/StringBuilder;-><init>()V

    move-object/from16 v14, p4

    invoke-virtual {v6, v14}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    const-string v7, ";"

    invoke-virtual {v6, v7}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    invoke-virtual {v6, v9}, Ljava/lang/StringBuilder;->append(Ljava/lang/Object;)Ljava/lang/StringBuilder;

    invoke-virtual {v6, v7}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    invoke-virtual {v6, v3}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    invoke-virtual {v6}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;

    move-result-object v6

    invoke-static {v13, v6}, Landroid/util/Log;->d(Ljava/lang/String;Ljava/lang/String;)I

    .line 225
    const/4 v0, 0x1

    goto :goto_1

    .line 222
    :cond_1
    move-object/from16 v14, p4

    .line 227
    .end local v5    # "piiString":Ljava/lang/String;
    :goto_1
    goto :goto_0

    .line 221
    :cond_2
    move-object/from16 v14, p4

    goto :goto_2

    .line 217
    .end local v3    # "stringInstance":Ljava/lang/String;
    :cond_3
    move-object/from16 v14, p4

    .line 232
    :goto_2
    const/4 v15, 0x1

    if-lt v2, v15, :cond_5

    .line 233
    invoke-interface/range {p3 .. p3}, Ljava/util/List;->size()I

    move-result v3

    sub-int/2addr v3, v15

    invoke-interface {v9, v3}, Ljava/util/List;->remove(I)Ljava/lang/Object;

    .line 234
    if-eqz v0, :cond_4

    .line 235
    return p5

    .line 238
    :cond_4
    return v10

    .line 244
    :cond_5
    invoke-virtual {v11}, Ljava/lang/Class;->getDeclaredFields()[Ljava/lang/reflect/Field;

    move-result-object v8

    .line 245
    .local v8, "fields":[Ljava/lang/reflect/Field;
    array-length v7, v8

    const/16 v16, 0x0

    move/from16 v17, v0

    const/4 v6, 0x0

    .end local v0    # "childFoundLeak":Z
    .local v17, "childFoundLeak":Z
    :goto_3
    if-ge v6, v7, :cond_15

    aget-object v5, v8, v6

    .line 248
    .local v5, "field":Ljava/lang/reflect/Field;
    const/4 v3, 0x0

    .line 251
    .local v3, "canAccess":Z
    :try_start_0
    invoke-virtual {v5, v15}, Ljava/lang/reflect/Field;->setAccessible(Z)V
    :try_end_0
    .catch Ljava/lang/SecurityException; {:try_start_0 .. :try_end_0} :catch_0

    .line 252
    const/4 v3, 0x1

    .line 266
    move/from16 v18, v3

    goto :goto_4

    .line 254
    :catch_0
    move-exception v0

    move-object v4, v0

    move-object v0, v4

    .line 257
    .local v0, "e":Ljava/lang/SecurityException;
    const-string v4, "opens ([\\w.]+)"

    const/4 v10, 0x2

    invoke-static {v4, v10}, Ljava/util/regex/Pattern;->compile(Ljava/lang/String;I)Ljava/util/regex/Pattern;

    move-result-object v4

    .line 258
    .local v4, "pattern":Ljava/util/regex/Pattern;
    invoke-virtual {v0}, Ljava/lang/SecurityException;->getMessage()Ljava/lang/String;

    move-result-object v10

    invoke-virtual {v4, v10}, Ljava/util/regex/Pattern;->matcher(Ljava/lang/CharSequence;)Ljava/util/regex/Matcher;

    move-result-object v10

    .line 259
    .local v10, "matcher":Ljava/util/regex/Matcher;
    invoke-virtual {v10}, Ljava/util/regex/Matcher;->find()Z

    move-result v19

    if-eqz v19, :cond_6

    .line 260
    invoke-virtual {v10, v15}, Ljava/util/regex/Matcher;->group(I)Ljava/lang/String;

    move-result-object v19

    .line 261
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

    invoke-static {v13, v3}, Landroid/util/Log;->d(Ljava/lang/String;Ljava/lang/String;)I

    .line 262
    .end local v19    # "closedPackageName":Ljava/lang/String;
    goto :goto_4

    .line 264
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

    invoke-static {v13, v3}, Landroid/util/Log;->d(Ljava/lang/String;Ljava/lang/String;)I

    .line 268
    .end local v0    # "e":Ljava/lang/SecurityException;
    .end local v4    # "pattern":Ljava/util/regex/Pattern;
    .end local v10    # "matcher":Ljava/util/regex/Matcher;
    :goto_4
    if-eqz v18, :cond_14

    .line 270
    const/4 v0, 0x0

    .line 271
    .local v0, "fieldInstance":Ljava/lang/Object;
    :try_start_1
    invoke-virtual {v5}, Ljava/lang/reflect/Field;->getModifiers()I

    move-result v3

    invoke-static {v3}, Ljava/lang/reflect/Modifier;->isStatic(I)Z

    move-result v3
    :try_end_1
    .catch Ljava/lang/IllegalAccessException; {:try_start_1 .. :try_end_1} :catch_3

    if-eqz v3, :cond_7

    .line 272
    const/4 v3, 0x0

    :try_start_2
    invoke-virtual {v5, v3}, Ljava/lang/reflect/Field;->get(Ljava/lang/Object;)Ljava/lang/Object;

    move-result-object v3
    :try_end_2
    .catch Ljava/lang/IllegalAccessException; {:try_start_2 .. :try_end_2} :catch_1

    move-object v0, v3

    goto :goto_5

    .line 333
    .end local v0    # "fieldInstance":Ljava/lang/Object;
    :catch_1
    move-exception v0

    move-object/from16 v20, v5

    move-object/from16 v22, v8

    goto/16 :goto_a

    .line 275
    .restart local v0    # "fieldInstance":Ljava/lang/Object;
    :cond_7
    :try_start_3
    invoke-virtual {v5, v1}, Ljava/lang/reflect/Field;->get(Ljava/lang/Object;)Ljava/lang/Object;

    move-result-object v3

    move-object v0, v3

    .line 278
    :goto_5
    if-nez v0, :cond_8

    .line 279
    move/from16 v19, v6

    move/from16 v21, v7

    move-object/from16 v22, v8

    goto/16 :goto_b

    .line 282
    :cond_8
    invoke-virtual {v0}, Ljava/lang/Object;->getClass()Ljava/lang/Class;

    move-result-object v3

    move-object v10, v3

    .line 290
    .local v10, "fieldClass":Ljava/lang/Class;, "Ljava/lang/Class<*>;"
    invoke-virtual {v10}, Ljava/lang/Class;->isPrimitive()Z

    move-result v3

    if-eqz v3, :cond_9

    .line 292
    move/from16 v19, v6

    move/from16 v21, v7

    move-object/from16 v22, v8

    goto/16 :goto_b

    .line 294
    :cond_9
    sget-object v3, Ledu/utsa/sefm/heapsnapshot/Snapshot;->EXCLUDED_CLASSES:Ljava/util/List;

    invoke-interface {v3, v10}, Ljava/util/List;->contains(Ljava/lang/Object;)Z

    move-result v3

    if-eqz v3, :cond_a

    .line 296
    move/from16 v19, v6

    move/from16 v21, v7

    move-object/from16 v22, v8

    goto/16 :goto_b

    .line 298
    :cond_a
    const-class v3, Ljava/util/Collection;

    invoke-virtual {v3, v10}, Ljava/lang/Class;->isAssignableFrom(Ljava/lang/Class;)Z

    move-result v3

    if-eqz v3, :cond_d

    .line 299
    move-object v3, v0

    check-cast v3, Ljava/util/Collection;

    move-object v15, v3

    .line 300
    .local v15, "collectionInstance":Ljava/util/Collection;, "Ljava/util/Collection<*>;"
    new-instance v3, Ledu/utsa/sefm/heapsnapshot/Snapshot$FieldInfo;

    invoke-virtual {v10}, Ljava/lang/Class;->getName()Ljava/lang/String;

    move-result-object v4

    invoke-virtual {v5}, Ljava/lang/reflect/Field;->getName()Ljava/lang/String;

    move-result-object v1

    invoke-direct {v3, v4, v1}, Ledu/utsa/sefm/heapsnapshot/Snapshot$FieldInfo;-><init>(Ljava/lang/String;Ljava/lang/String;)V

    invoke-interface {v9, v3}, Ljava/util/List;->add(Ljava/lang/Object;)Z

    .line 302
    invoke-interface {v15}, Ljava/util/Collection;->iterator()Ljava/util/Iterator;

    move-result-object v1

    :goto_6
    invoke-interface {v1}, Ljava/util/Iterator;->hasNext()Z

    move-result v3

    if-eqz v3, :cond_c

    invoke-interface {v1}, Ljava/util/Iterator;->next()Ljava/lang/Object;

    move-result-object v3

    .line 303
    .local v3, "o":Ljava/lang/Object;
    const-string v4, "collectionElement"
    :try_end_3
    .catch Ljava/lang/IllegalAccessException; {:try_start_3 .. :try_end_3} :catch_3

    add-int/lit8 v19, v2, 0x1

    move-object/from16 v20, v5

    .end local v5    # "field":Ljava/lang/reflect/Field;
    .local v20, "field":Ljava/lang/reflect/Field;
    move/from16 v5, v19

    move/from16 v19, v6

    move-object/from16 v6, p3

    move/from16 v21, v7

    move-object/from16 v7, p4

    move-object/from16 v22, v8

    .end local v8    # "fields":[Ljava/lang/reflect/Field;
    .local v22, "fields":[Ljava/lang/reflect/Field;
    move/from16 v8, p5

    :try_start_4
    invoke-static/range {v3 .. v8}, Ledu/utsa/sefm/heapsnapshot/Snapshot;->checkObjectForPIIRecursive(Ljava/lang/Object;Ljava/lang/String;ILjava/util/List;Ljava/lang/String;I)I

    move-result v4

    .line 304
    .local v4, "result":I
    const/4 v5, -0x1

    if-eq v4, v5, :cond_b

    .line 305
    const/4 v5, 0x1

    move/from16 v17, v5

    .line 307
    .end local v3    # "o":Ljava/lang/Object;
    .end local v4    # "result":I
    :cond_b
    move/from16 v6, v19

    move-object/from16 v5, v20

    move/from16 v7, v21

    move-object/from16 v8, v22

    goto :goto_6

    .line 308
    .end local v20    # "field":Ljava/lang/reflect/Field;
    .end local v22    # "fields":[Ljava/lang/reflect/Field;
    .restart local v5    # "field":Ljava/lang/reflect/Field;
    .restart local v8    # "fields":[Ljava/lang/reflect/Field;
    :cond_c
    move-object/from16 v20, v5

    move/from16 v19, v6

    move/from16 v21, v7

    move-object/from16 v22, v8

    .end local v5    # "field":Ljava/lang/reflect/Field;
    .end local v8    # "fields":[Ljava/lang/reflect/Field;
    .restart local v20    # "field":Ljava/lang/reflect/Field;
    .restart local v22    # "fields":[Ljava/lang/reflect/Field;
    invoke-interface/range {p3 .. p3}, Ljava/util/List;->size()I

    move-result v1

    const/4 v3, 0x1

    sub-int/2addr v1, v3

    invoke-interface {v9, v1}, Ljava/util/List;->remove(I)Ljava/lang/Object;

    .line 309
    nop

    .end local v15    # "collectionInstance":Ljava/util/Collection;, "Ljava/util/Collection<*>;"
    goto/16 :goto_9

    .line 310
    .end local v20    # "field":Ljava/lang/reflect/Field;
    .end local v22    # "fields":[Ljava/lang/reflect/Field;
    .restart local v5    # "field":Ljava/lang/reflect/Field;
    .restart local v8    # "fields":[Ljava/lang/reflect/Field;
    :cond_d
    move-object/from16 v20, v5

    move/from16 v19, v6

    move/from16 v21, v7

    move-object/from16 v22, v8

    .end local v5    # "field":Ljava/lang/reflect/Field;
    .end local v8    # "fields":[Ljava/lang/reflect/Field;
    .restart local v20    # "field":Ljava/lang/reflect/Field;
    .restart local v22    # "fields":[Ljava/lang/reflect/Field;
    const-class v1, Ljava/util/Map;

    invoke-virtual {v1, v10}, Ljava/lang/Class;->isAssignableFrom(Ljava/lang/Class;)Z

    move-result v1

    if-eqz v1, :cond_12

    .line 311
    move-object v1, v0

    check-cast v1, Ljava/util/Map;

    .line 312
    .local v1, "mapInstance":Ljava/util/Map;, "Ljava/util/Map<**>;"
    new-instance v3, Ledu/utsa/sefm/heapsnapshot/Snapshot$FieldInfo;

    invoke-virtual {v10}, Ljava/lang/Class;->getName()Ljava/lang/String;

    move-result-object v4

    invoke-virtual/range {v20 .. v20}, Ljava/lang/reflect/Field;->getName()Ljava/lang/String;

    move-result-object v5

    invoke-direct {v3, v4, v5}, Ledu/utsa/sefm/heapsnapshot/Snapshot$FieldInfo;-><init>(Ljava/lang/String;Ljava/lang/String;)V

    invoke-interface {v9, v3}, Ljava/util/List;->add(Ljava/lang/Object;)Z

    .line 313
    invoke-interface {v1}, Ljava/util/Map;->keySet()Ljava/util/Set;

    move-result-object v3

    invoke-interface {v3}, Ljava/util/Set;->iterator()Ljava/util/Iterator;

    move-result-object v15

    :goto_7
    invoke-interface {v15}, Ljava/util/Iterator;->hasNext()Z

    move-result v3

    if-eqz v3, :cond_f

    invoke-interface {v15}, Ljava/util/Iterator;->next()Ljava/lang/Object;

    move-result-object v3

    .line 314
    .restart local v3    # "o":Ljava/lang/Object;
    const-string v4, "mapKey"

    add-int/lit8 v5, v2, 0x1

    move-object/from16 v6, p3

    move-object/from16 v7, p4

    move/from16 v8, p5

    invoke-static/range {v3 .. v8}, Ledu/utsa/sefm/heapsnapshot/Snapshot;->checkObjectForPIIRecursive(Ljava/lang/Object;Ljava/lang/String;ILjava/util/List;Ljava/lang/String;I)I

    move-result v4

    .line 315
    .restart local v4    # "result":I
    const/4 v5, -0x1

    if-eq v4, v5, :cond_e

    .line 316
    const/4 v5, 0x1

    move/from16 v17, v5

    .line 318
    .end local v3    # "o":Ljava/lang/Object;
    .end local v4    # "result":I
    :cond_e
    goto :goto_7

    .line 319
    :cond_f
    invoke-interface {v1}, Ljava/util/Map;->values()Ljava/util/Collection;

    move-result-object v3

    invoke-interface {v3}, Ljava/util/Collection;->iterator()Ljava/util/Iterator;

    move-result-object v15

    :goto_8
    invoke-interface {v15}, Ljava/util/Iterator;->hasNext()Z

    move-result v3

    if-eqz v3, :cond_11

    invoke-interface {v15}, Ljava/util/Iterator;->next()Ljava/lang/Object;

    move-result-object v3

    .line 320
    .restart local v3    # "o":Ljava/lang/Object;
    const-string v4, "mapValue"

    add-int/lit8 v5, v2, 0x1

    move-object/from16 v6, p3

    move-object/from16 v7, p4

    move/from16 v8, p5

    invoke-static/range {v3 .. v8}, Ledu/utsa/sefm/heapsnapshot/Snapshot;->checkObjectForPIIRecursive(Ljava/lang/Object;Ljava/lang/String;ILjava/util/List;Ljava/lang/String;I)I

    move-result v4

    .line 321
    .restart local v4    # "result":I
    const/4 v5, -0x1

    if-eq v4, v5, :cond_10

    .line 322
    const/16 v17, 0x1

    .line 324
    .end local v3    # "o":Ljava/lang/Object;
    .end local v4    # "result":I
    :cond_10
    goto :goto_8

    .line 325
    :cond_11
    invoke-interface/range {p3 .. p3}, Ljava/util/List;->size()I

    move-result v3

    const/4 v4, 0x1

    sub-int/2addr v3, v4

    invoke-interface {v9, v3}, Ljava/util/List;->remove(I)Ljava/lang/Object;

    .line 326
    nop

    .end local v1    # "mapInstance":Ljava/util/Map;, "Ljava/util/Map<**>;"
    goto :goto_9

    .line 328
    :cond_12
    invoke-virtual/range {v20 .. v20}, Ljava/lang/reflect/Field;->getName()Ljava/lang/String;

    move-result-object v4

    add-int/lit8 v5, v2, 0x1

    move-object v3, v0

    move-object/from16 v6, p3

    move-object/from16 v7, p4

    move/from16 v8, p5

    invoke-static/range {v3 .. v8}, Ledu/utsa/sefm/heapsnapshot/Snapshot;->checkObjectForPIIRecursive(Ljava/lang/Object;Ljava/lang/String;ILjava/util/List;Ljava/lang/String;I)I

    move-result v1
    :try_end_4
    .catch Ljava/lang/IllegalAccessException; {:try_start_4 .. :try_end_4} :catch_2

    .line 329
    .local v1, "result":I
    const/4 v3, -0x1

    if-eq v1, v3, :cond_13

    .line 330
    const/16 v17, 0x1

    .line 335
    .end local v0    # "fieldInstance":Ljava/lang/Object;
    .end local v1    # "result":I
    .end local v10    # "fieldClass":Ljava/lang/Class;, "Ljava/lang/Class<*>;"
    :cond_13
    :goto_9
    goto :goto_b

    .line 333
    :catch_2
    move-exception v0

    goto :goto_a

    .end local v20    # "field":Ljava/lang/reflect/Field;
    .end local v22    # "fields":[Ljava/lang/reflect/Field;
    .restart local v5    # "field":Ljava/lang/reflect/Field;
    .restart local v8    # "fields":[Ljava/lang/reflect/Field;
    :catch_3
    move-exception v0

    move-object/from16 v20, v5

    move-object/from16 v22, v8

    .line 334
    .end local v5    # "field":Ljava/lang/reflect/Field;
    .end local v8    # "fields":[Ljava/lang/reflect/Field;
    .local v0, "e":Ljava/lang/IllegalAccessException;
    .restart local v20    # "field":Ljava/lang/reflect/Field;
    .restart local v22    # "fields":[Ljava/lang/reflect/Field;
    :goto_a
    new-instance v1, Ljava/lang/RuntimeException;

    invoke-direct {v1, v0}, Ljava/lang/RuntimeException;-><init>(Ljava/lang/Throwable;)V

    throw v1

    .line 268
    .end local v0    # "e":Ljava/lang/IllegalAccessException;
    .end local v20    # "field":Ljava/lang/reflect/Field;
    .end local v22    # "fields":[Ljava/lang/reflect/Field;
    .restart local v5    # "field":Ljava/lang/reflect/Field;
    .restart local v8    # "fields":[Ljava/lang/reflect/Field;
    :cond_14
    move-object/from16 v20, v5

    move/from16 v19, v6

    move/from16 v21, v7

    move-object/from16 v22, v8

    .line 245
    .end local v5    # "field":Ljava/lang/reflect/Field;
    .end local v8    # "fields":[Ljava/lang/reflect/Field;
    .end local v18    # "canAccess":Z
    .restart local v22    # "fields":[Ljava/lang/reflect/Field;
    :goto_b
    add-int/lit8 v6, v19, 0x1

    move-object/from16 v1, p0

    move/from16 v7, v21

    move-object/from16 v8, v22

    const/4 v10, -0x1

    const/4 v15, 0x1

    goto/16 :goto_3

    .line 340
    .end local v22    # "fields":[Ljava/lang/reflect/Field;
    .restart local v8    # "fields":[Ljava/lang/reflect/Field;
    :cond_15
    move-object/from16 v22, v8

    .end local v8    # "fields":[Ljava/lang/reflect/Field;
    .restart local v22    # "fields":[Ljava/lang/reflect/Field;
    invoke-interface/range {p3 .. p3}, Ljava/util/List;->size()I

    move-result v0

    const/4 v1, 0x1

    sub-int/2addr v0, v1

    invoke-interface {v9, v0}, Ljava/util/List;->remove(I)Ljava/lang/Object;

    .line 341
    if-eqz v17, :cond_16

    .line 342
    return p5

    .line 345
    :cond_16
    const/4 v1, -0x1

    return v1
.end method

.method public static largeLog(Ljava/lang/String;Ljava/lang/String;)V
    .locals 2
    .param p0, "tag"    # Ljava/lang/String;
    .param p1, "content"    # Ljava/lang/String;

    .line 366
    invoke-virtual {p1}, Ljava/lang/String;->length()I

    move-result v0

    const/16 v1, 0xfa0

    if-le v0, v1, :cond_0

    .line 367
    const/4 v0, 0x0

    invoke-virtual {p1, v0, v1}, Ljava/lang/String;->substring(II)Ljava/lang/String;

    move-result-object v0

    invoke-static {p0, v0}, Landroid/util/Log;->d(Ljava/lang/String;Ljava/lang/String;)I

    .line 368
    invoke-virtual {p1, v1}, Ljava/lang/String;->substring(I)Ljava/lang/String;

    move-result-object v0

    invoke-static {p0, v0}, Ledu/utsa/sefm/heapsnapshot/Snapshot;->largeLog(Ljava/lang/String;Ljava/lang/String;)V

    goto :goto_0

    .line 370
    :cond_0
    invoke-static {p0, p1}, Landroid/util/Log;->d(Ljava/lang/String;Ljava/lang/String;)I

    .line 372
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

    .line 38
    new-instance v0, Lorg/json/JSONObject;

    invoke-direct {v0}, Lorg/json/JSONObject;-><init>()V

    .line 40
    .local v0, "resultJson":Lorg/json/JSONObject;
    invoke-virtual {p0}, Ljava/lang/Object;->getClass()Ljava/lang/Class;

    move-result-object v1

    .line 41
    .local v1, "objClass":Ljava/lang/Class;, "Ljava/lang/Class<*>;"
    invoke-virtual {v1}, Ljava/lang/Class;->getName()Ljava/lang/String;

    move-result-object v2

    const-string v3, "class_name"

    invoke-virtual {v0, v3, v2}, Lorg/json/JSONObject;->put(Ljava/lang/String;Ljava/lang/Object;)Lorg/json/JSONObject;

    .line 42
    invoke-virtual {v1}, Ljava/lang/Class;->getModifiers()I

    move-result v2

    const-string v3, "modifiers"

    invoke-virtual {v0, v3, v2}, Lorg/json/JSONObject;->put(Ljava/lang/String;I)Lorg/json/JSONObject;

    .line 44
    invoke-virtual {p0}, Ljava/lang/Object;->hashCode()I

    move-result v2

    const-string v3, "hash_code"

    invoke-virtual {v0, v3, v2}, Lorg/json/JSONObject;->put(Ljava/lang/String;I)Lorg/json/JSONObject;

    .line 47
    invoke-virtual {v1}, Ljava/lang/Class;->getDeclaredFields()[Ljava/lang/reflect/Field;

    move-result-object v2

    .line 52
    .local v2, "fields":[Ljava/lang/reflect/Field;
    array-length v3, v2

    const/4 v4, 0x0

    :goto_0
    if-ge v4, v3, :cond_4

    aget-object v5, v2, v4

    .line 53
    .local v5, "field":Ljava/lang/reflect/Field;
    invoke-virtual {v5}, Ljava/lang/reflect/Field;->getName()Ljava/lang/String;

    move-result-object v6

    .line 57
    .local v6, "fieldName":Ljava/lang/String;
    const/4 v7, 0x1

    invoke-virtual {v5, v7}, Ljava/lang/reflect/Field;->setAccessible(Z)V

    .line 80
    const/4 v8, 0x1

    .line 81
    .local v8, "canAccess":Z
    if-eqz v8, :cond_3

    .line 84
    const/4 v9, 0x0

    .line 85
    .local v9, "child":Ljava/lang/Object;
    :try_start_0
    invoke-virtual {v5}, Ljava/lang/reflect/Field;->getModifiers()I

    move-result v10

    invoke-static {v10}, Ljava/lang/reflect/Modifier;->isStatic(I)Z

    move-result v10

    const/4 v11, 0x0

    if-eqz v10, :cond_0

    .line 86
    invoke-virtual {v5, v11}, Ljava/lang/reflect/Field;->get(Ljava/lang/Object;)Ljava/lang/Object;

    move-result-object v10

    move-object v9, v10

    goto :goto_1

    .line 89
    :cond_0
    invoke-virtual {v5, p0}, Ljava/lang/reflect/Field;->get(Ljava/lang/Object;)Ljava/lang/Object;

    move-result-object v10

    move-object v9, v10

    .line 93
    :goto_1
    if-nez v9, :cond_1

    .line 94
    move-object v7, v11

    check-cast v7, Ljava/util/Map;

    invoke-virtual {v0, v6, v11}, Lorg/json/JSONObject;->put(Ljava/lang/String;Ljava/lang/Object;)Lorg/json/JSONObject;

    goto :goto_2

    .line 97
    :cond_1
    if-le p1, v7, :cond_2

    .line 98
    add-int/lit8 v7, p1, -0x1

    invoke-static {v9, v7}, Ledu/utsa/sefm/heapsnapshot/Snapshot;->takeSnapshot(Ljava/lang/Object;I)Lorg/json/JSONObject;

    move-result-object v7

    invoke-virtual {v0, v6, v7}, Lorg/json/JSONObject;->put(Ljava/lang/String;Ljava/lang/Object;)Lorg/json/JSONObject;

    goto :goto_2

    .line 101
    :cond_2
    const-string v7, "*"

    invoke-virtual {v0, v6, v7}, Lorg/json/JSONObject;->put(Ljava/lang/String;Ljava/lang/Object;)Lorg/json/JSONObject;
    :try_end_0
    .catch Ljava/lang/IllegalAccessException; {:try_start_0 .. :try_end_0} :catch_0

    .line 106
    .end local v9    # "child":Ljava/lang/Object;
    :goto_2
    goto :goto_3

    .line 104
    :catch_0
    move-exception v3

    .line 105
    .local v3, "e":Ljava/lang/IllegalAccessException;
    new-instance v4, Ljava/lang/RuntimeException;

    invoke-direct {v4, v3}, Ljava/lang/RuntimeException;-><init>(Ljava/lang/Throwable;)V

    throw v4

    .line 52
    .end local v3    # "e":Ljava/lang/IllegalAccessException;
    .end local v5    # "field":Ljava/lang/reflect/Field;
    .end local v6    # "fieldName":Ljava/lang/String;
    .end local v8    # "canAccess":Z
    :cond_3
    :goto_3
    add-int/lit8 v4, v4, 0x1

    goto :goto_0

    .line 110
    :cond_4
    return-object v0
.end method
