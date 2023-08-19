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
.field private static final EXCLUDED_CLASSES:Ljava/util/List;
    .annotation system Ldalvik/annotation/Signature;
        value = {
            "Ljava/util/List<",
            "Ljava/lang/Class<",
            "*>;>;"
        }
    .end annotation
.end field

.field private static final INSPECTION_DEPTH:I = 0x3

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

.field private static callID:I


# direct methods
.method static constructor <clinit>()V
    .locals 4

    .line 24
    const-string v0, "8901240197155182897"

    const-string v1, "355458061189396"

    filled-new-array {v0, v1}, [Ljava/lang/String;

    move-result-object v0

    invoke-static {v0}, Ljava/util/Arrays;->asList([Ljava/lang/Object;)Ljava/util/List;

    move-result-object v0

    sput-object v0, Ledu/utsa/sefm/heapsnapshot/Snapshot;->PII:Ljava/util/List;

    .line 25
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

    .line 27
    sput v2, Ledu/utsa/sefm/heapsnapshot/Snapshot;->callID:I

    return-void
.end method

.method public constructor <init>()V
    .locals 0

    .line 22
    invoke-direct {p0}, Ljava/lang/Object;-><init>()V

    return-void
.end method

.method public static checkObjectForPII(Ljava/lang/Object;Ljava/lang/String;)I
    .locals 3
    .param p0, "instance"    # Ljava/lang/Object;
    .param p1, "invocationDescription"    # Ljava/lang/String;

    .line 111
    const/4 v0, 0x0

    .line 112
    .local v0, "currentInspectionDepth":I
    new-instance v1, Ljava/util/ArrayList;

    invoke-direct {v1}, Ljava/util/ArrayList;-><init>()V

    .line 113
    .local v1, "accessPath":Ljava/util/List;, "Ljava/util/List<Ledu/utsa/sefm/heapsnapshot/Snapshot$FieldInfo;>;"
    sget v2, Ledu/utsa/sefm/heapsnapshot/Snapshot;->callID:I

    add-int/lit8 v2, v2, 0x1

    sput v2, Ledu/utsa/sefm/heapsnapshot/Snapshot;->callID:I

    .line 115
    if-nez p0, :cond_0

    .line 116
    const/4 v2, -0x1

    return v2

    .line 119
    :cond_0
    const-string v2, "."

    invoke-static {p0, v2, v0, v1, p1}, Ledu/utsa/sefm/heapsnapshot/Snapshot;->checkObjectForPIIRecursive(Ljava/lang/Object;Ljava/lang/String;ILjava/util/List;Ljava/lang/String;)I

    move-result v2

    return v2
.end method

.method private static checkObjectForPIIRecursive(Ljava/lang/Object;Ljava/lang/String;ILjava/util/List;Ljava/lang/String;)I
    .locals 21
    .param p0, "instance"    # Ljava/lang/Object;
    .param p1, "instanceName"    # Ljava/lang/String;
    .param p2, "curDepth"    # I
    .param p4, "invocationDescription"    # Ljava/lang/String;
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
            ")I"
        }
    .end annotation

    .line 130
    .local p3, "accessPath":Ljava/util/List;, "Ljava/util/List<Ledu/utsa/sefm/heapsnapshot/Snapshot$FieldInfo;>;"
    move-object/from16 v1, p0

    move/from16 v2, p2

    move-object/from16 v3, p3

    move-object/from16 v4, p4

    const/4 v5, -0x1

    if-nez v1, :cond_0

    .line 131
    return v5

    .line 133
    :cond_0
    invoke-virtual/range {p0 .. p0}, Ljava/lang/Object;->getClass()Ljava/lang/Class;

    move-result-object v6

    .line 134
    .local v6, "objClass":Ljava/lang/Class;, "Ljava/lang/Class<*>;"
    new-instance v0, Ledu/utsa/sefm/heapsnapshot/Snapshot$FieldInfo;

    invoke-virtual {v6}, Ljava/lang/Class;->getName()Ljava/lang/String;

    move-result-object v7

    move-object/from16 v8, p1

    invoke-direct {v0, v7, v8}, Ledu/utsa/sefm/heapsnapshot/Snapshot$FieldInfo;-><init>(Ljava/lang/String;Ljava/lang/String;)V

    invoke-interface {v3, v0}, Ljava/util/List;->add(Ljava/lang/Object;)Z

    .line 135
    const/4 v0, 0x0

    .line 142
    .local v0, "childFoundLeak":Z
    const-class v7, Ljava/lang/String;

    invoke-virtual {v6, v7}, Ljava/lang/Object;->equals(Ljava/lang/Object;)Z

    move-result v7

    const-string v9, "Snapshot"

    if-eqz v7, :cond_1

    .line 144
    move-object v7, v1

    check-cast v7, Ljava/lang/String;

    .line 146
    .local v7, "stringInstance":Ljava/lang/String;
    sget-object v10, Ledu/utsa/sefm/heapsnapshot/Snapshot;->PII:Ljava/util/List;

    invoke-interface {v10, v7}, Ljava/util/List;->contains(Ljava/lang/Object;)Z

    move-result v10

    if-eqz v10, :cond_1

    .line 148
    new-instance v10, Ljava/lang/StringBuilder;

    invoke-direct {v10}, Ljava/lang/StringBuilder;-><init>()V

    invoke-virtual {v10, v4}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    const-string v11, ";"

    invoke-virtual {v10, v11}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    invoke-virtual {v10, v3}, Ljava/lang/StringBuilder;->append(Ljava/lang/Object;)Ljava/lang/StringBuilder;

    invoke-virtual {v10, v11}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    invoke-virtual {v10, v7}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    invoke-virtual {v10}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;

    move-result-object v10

    invoke-static {v9, v10}, Landroid/util/Log;->d(Ljava/lang/String;Ljava/lang/String;)I

    .line 149
    const/4 v0, 0x1

    .line 154
    .end local v7    # "stringInstance":Ljava/lang/String;
    :cond_1
    const/4 v7, 0x3

    const/4 v10, 0x1

    if-lt v2, v7, :cond_3

    .line 155
    invoke-interface/range {p3 .. p3}, Ljava/util/List;->size()I

    move-result v7

    sub-int/2addr v7, v10

    invoke-interface {v3, v7}, Ljava/util/List;->remove(I)Ljava/lang/Object;

    .line 156
    if-eqz v0, :cond_2

    .line 157
    sget v5, Ledu/utsa/sefm/heapsnapshot/Snapshot;->callID:I

    return v5

    .line 160
    :cond_2
    return v5

    .line 166
    :cond_3
    invoke-virtual {v6}, Ljava/lang/Class;->getDeclaredFields()[Ljava/lang/reflect/Field;

    move-result-object v7

    .line 167
    .local v7, "fields":[Ljava/lang/reflect/Field;
    array-length v11, v7

    move v13, v0

    const/4 v14, 0x0

    .end local v0    # "childFoundLeak":Z
    .local v13, "childFoundLeak":Z
    :goto_0
    if-ge v14, v11, :cond_13

    aget-object v15, v7, v14

    .line 171
    .local v15, "field":Ljava/lang/reflect/Field;
    const/16 v16, 0x0

    .line 173
    .local v16, "canAccess":Z
    :try_start_0
    invoke-virtual {v15, v10}, Ljava/lang/reflect/Field;->setAccessible(Z)V
    :try_end_0
    .catch Ljava/lang/SecurityException; {:try_start_0 .. :try_end_0} :catch_0

    .line 174
    const/16 v16, 0x1

    .line 188
    const/16 v18, 0x0

    goto :goto_1

    .line 176
    :catch_0
    move-exception v0

    move-object/from16 v17, v0

    move-object/from16 v0, v17

    .line 179
    .local v0, "e":Ljava/lang/SecurityException;
    const-string v5, "opens ([\\w.]+)"

    const/4 v12, 0x2

    invoke-static {v5, v12}, Ljava/util/regex/Pattern;->compile(Ljava/lang/String;I)Ljava/util/regex/Pattern;

    move-result-object v5

    .line 180
    .local v5, "pattern":Ljava/util/regex/Pattern;
    invoke-virtual {v0}, Ljava/lang/SecurityException;->getMessage()Ljava/lang/String;

    move-result-object v12

    invoke-virtual {v5, v12}, Ljava/util/regex/Pattern;->matcher(Ljava/lang/CharSequence;)Ljava/util/regex/Matcher;

    move-result-object v12

    .line 181
    .local v12, "matcher":Ljava/util/regex/Matcher;
    invoke-virtual {v12}, Ljava/util/regex/Matcher;->find()Z

    move-result v20

    if-eqz v20, :cond_4

    .line 182
    invoke-virtual {v12, v10}, Ljava/util/regex/Matcher;->group(I)Ljava/lang/String;

    move-result-object v20

    .line 183
    .local v20, "closedPackageName":Ljava/lang/String;
    const/4 v10, 0x2

    new-array v10, v10, [Ljava/lang/Object;

    const/16 v18, 0x0

    aput-object v20, v10, v18

    const/16 v19, 0x1

    aput-object v15, v10, v19

    move-object/from16 v19, v5

    .end local v5    # "pattern":Ljava/util/regex/Pattern;
    .local v19, "pattern":Ljava/util/regex/Pattern;
    const-string v5, "Closed Package %s in Field %s"

    invoke-static {v5, v10}, Ljava/lang/String;->format(Ljava/lang/String;[Ljava/lang/Object;)Ljava/lang/String;

    move-result-object v5

    invoke-static {v9, v5}, Landroid/util/Log;->d(Ljava/lang/String;Ljava/lang/String;)I

    .line 184
    .end local v20    # "closedPackageName":Ljava/lang/String;
    goto :goto_1

    .line 186
    .end local v19    # "pattern":Ljava/util/regex/Pattern;
    .restart local v5    # "pattern":Ljava/util/regex/Pattern;
    :cond_4
    move-object/from16 v19, v5

    const/16 v18, 0x0

    .end local v5    # "pattern":Ljava/util/regex/Pattern;
    .restart local v19    # "pattern":Ljava/util/regex/Pattern;
    new-instance v5, Ljava/lang/StringBuilder;

    invoke-direct {v5}, Ljava/lang/StringBuilder;-><init>()V

    const-string v10, "Some unrecognized Closed Package! "

    invoke-virtual {v5, v10}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    invoke-virtual {v0}, Ljava/lang/SecurityException;->getMessage()Ljava/lang/String;

    move-result-object v10

    invoke-virtual {v5, v10}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    invoke-virtual {v5}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;

    move-result-object v5

    invoke-static {v9, v5}, Landroid/util/Log;->d(Ljava/lang/String;Ljava/lang/String;)I

    .line 191
    .end local v0    # "e":Ljava/lang/SecurityException;
    .end local v12    # "matcher":Ljava/util/regex/Matcher;
    .end local v19    # "pattern":Ljava/util/regex/Pattern;
    :goto_1
    if-eqz v16, :cond_12

    .line 193
    const/4 v0, 0x0

    .line 194
    .local v0, "fieldInstance":Ljava/lang/Object;
    :try_start_1
    invoke-virtual {v15}, Ljava/lang/reflect/Field;->getModifiers()I

    move-result v5

    invoke-static {v5}, Ljava/lang/reflect/Modifier;->isStatic(I)Z

    move-result v5
    :try_end_1
    .catch Ljava/lang/IllegalAccessException; {:try_start_1 .. :try_end_1} :catch_3

    if-eqz v5, :cond_5

    .line 195
    const/4 v5, 0x0

    :try_start_2
    invoke-virtual {v15, v5}, Ljava/lang/reflect/Field;->get(Ljava/lang/Object;)Ljava/lang/Object;

    move-result-object v5
    :try_end_2
    .catch Ljava/lang/IllegalAccessException; {:try_start_2 .. :try_end_2} :catch_1

    move-object v0, v5

    goto :goto_2

    .line 256
    .end local v0    # "fieldInstance":Ljava/lang/Object;
    :catch_1
    move-exception v0

    move-object/from16 v19, v6

    goto/16 :goto_7

    .line 198
    .restart local v0    # "fieldInstance":Ljava/lang/Object;
    :cond_5
    :try_start_3
    invoke-virtual {v15, v1}, Ljava/lang/reflect/Field;->get(Ljava/lang/Object;)Ljava/lang/Object;

    move-result-object v5

    move-object v0, v5

    .line 201
    :goto_2
    if-nez v0, :cond_6

    .line 202
    move-object/from16 v19, v6

    goto/16 :goto_8

    .line 205
    :cond_6
    invoke-virtual {v0}, Ljava/lang/Object;->getClass()Ljava/lang/Class;

    move-result-object v5

    .line 213
    .local v5, "fieldClass":Ljava/lang/Class;, "Ljava/lang/Class<*>;"
    invoke-virtual {v5}, Ljava/lang/Class;->isPrimitive()Z

    move-result v10

    if-eqz v10, :cond_7

    .line 215
    move-object/from16 v19, v6

    goto/16 :goto_8

    .line 217
    :cond_7
    sget-object v10, Ledu/utsa/sefm/heapsnapshot/Snapshot;->EXCLUDED_CLASSES:Ljava/util/List;

    invoke-interface {v10, v5}, Ljava/util/List;->contains(Ljava/lang/Object;)Z

    move-result v10

    if-eqz v10, :cond_8

    .line 219
    move-object/from16 v19, v6

    goto/16 :goto_8

    .line 221
    :cond_8
    const-class v10, Ljava/util/Collection;

    invoke-virtual {v10, v5}, Ljava/lang/Class;->isAssignableFrom(Ljava/lang/Class;)Z

    move-result v10

    if-eqz v10, :cond_b

    .line 222
    move-object v10, v0

    check-cast v10, Ljava/util/Collection;

    .line 223
    .local v10, "collectionInstance":Ljava/util/Collection;, "Ljava/util/Collection<*>;"
    new-instance v12, Ledu/utsa/sefm/heapsnapshot/Snapshot$FieldInfo;

    invoke-virtual {v5}, Ljava/lang/Class;->getName()Ljava/lang/String;

    move-result-object v1
    :try_end_3
    .catch Ljava/lang/IllegalAccessException; {:try_start_3 .. :try_end_3} :catch_3

    move-object/from16 v19, v6

    .end local v6    # "objClass":Ljava/lang/Class;, "Ljava/lang/Class<*>;"
    .local v19, "objClass":Ljava/lang/Class;, "Ljava/lang/Class<*>;"
    :try_start_4
    invoke-virtual {v15}, Ljava/lang/reflect/Field;->getName()Ljava/lang/String;

    move-result-object v6

    invoke-direct {v12, v1, v6}, Ledu/utsa/sefm/heapsnapshot/Snapshot$FieldInfo;-><init>(Ljava/lang/String;Ljava/lang/String;)V

    invoke-interface {v3, v12}, Ljava/util/List;->add(Ljava/lang/Object;)Z

    .line 225
    invoke-interface {v10}, Ljava/util/Collection;->iterator()Ljava/util/Iterator;

    move-result-object v1

    :goto_3
    invoke-interface {v1}, Ljava/util/Iterator;->hasNext()Z

    move-result v6

    if-eqz v6, :cond_a

    invoke-interface {v1}, Ljava/util/Iterator;->next()Ljava/lang/Object;

    move-result-object v6

    .line 226
    .local v6, "o":Ljava/lang/Object;
    const-string v12, "collectionElement"

    move-object/from16 v20, v1

    add-int/lit8 v1, v2, 0x1

    invoke-static {v6, v12, v1, v3, v4}, Ledu/utsa/sefm/heapsnapshot/Snapshot;->checkObjectForPIIRecursive(Ljava/lang/Object;Ljava/lang/String;ILjava/util/List;Ljava/lang/String;)I

    move-result v1

    .line 227
    .local v1, "result":I
    const/4 v12, -0x1

    if-eq v1, v12, :cond_9

    .line 228
    const/4 v12, 0x1

    move v13, v12

    .line 230
    .end local v1    # "result":I
    .end local v6    # "o":Ljava/lang/Object;
    :cond_9
    move-object/from16 v1, v20

    goto :goto_3

    .line 231
    :cond_a
    invoke-interface/range {p3 .. p3}, Ljava/util/List;->size()I

    move-result v1

    const/4 v6, 0x1

    sub-int/2addr v1, v6

    invoke-interface {v3, v1}, Ljava/util/List;->remove(I)Ljava/lang/Object;

    .line 232
    nop

    .end local v10    # "collectionInstance":Ljava/util/Collection;, "Ljava/util/Collection<*>;"
    goto/16 :goto_6

    .line 233
    .end local v19    # "objClass":Ljava/lang/Class;, "Ljava/lang/Class<*>;"
    .local v6, "objClass":Ljava/lang/Class;, "Ljava/lang/Class<*>;"
    :cond_b
    move-object/from16 v19, v6

    .end local v6    # "objClass":Ljava/lang/Class;, "Ljava/lang/Class<*>;"
    .restart local v19    # "objClass":Ljava/lang/Class;, "Ljava/lang/Class<*>;"
    const-class v1, Ljava/util/Map;

    invoke-virtual {v1, v5}, Ljava/lang/Class;->isAssignableFrom(Ljava/lang/Class;)Z

    move-result v1

    if-eqz v1, :cond_10

    .line 234
    move-object v1, v0

    check-cast v1, Ljava/util/Map;

    .line 235
    .local v1, "mapInstance":Ljava/util/Map;, "Ljava/util/Map<**>;"
    new-instance v6, Ledu/utsa/sefm/heapsnapshot/Snapshot$FieldInfo;

    invoke-virtual {v5}, Ljava/lang/Class;->getName()Ljava/lang/String;

    move-result-object v10

    invoke-virtual {v15}, Ljava/lang/reflect/Field;->getName()Ljava/lang/String;

    move-result-object v12

    invoke-direct {v6, v10, v12}, Ledu/utsa/sefm/heapsnapshot/Snapshot$FieldInfo;-><init>(Ljava/lang/String;Ljava/lang/String;)V

    invoke-interface {v3, v6}, Ljava/util/List;->add(Ljava/lang/Object;)Z

    .line 236
    invoke-interface {v1}, Ljava/util/Map;->keySet()Ljava/util/Set;

    move-result-object v6

    invoke-interface {v6}, Ljava/util/Set;->iterator()Ljava/util/Iterator;

    move-result-object v6

    :goto_4
    invoke-interface {v6}, Ljava/util/Iterator;->hasNext()Z

    move-result v10

    if-eqz v10, :cond_d

    invoke-interface {v6}, Ljava/util/Iterator;->next()Ljava/lang/Object;

    move-result-object v10

    .line 237
    .local v10, "o":Ljava/lang/Object;
    const-string v12, "mapKey"

    move-object/from16 v20, v5

    .end local v5    # "fieldClass":Ljava/lang/Class;, "Ljava/lang/Class<*>;"
    .local v20, "fieldClass":Ljava/lang/Class;, "Ljava/lang/Class<*>;"
    add-int/lit8 v5, v2, 0x1

    invoke-static {v10, v12, v5, v3, v4}, Ledu/utsa/sefm/heapsnapshot/Snapshot;->checkObjectForPIIRecursive(Ljava/lang/Object;Ljava/lang/String;ILjava/util/List;Ljava/lang/String;)I

    move-result v5

    .line 238
    .local v5, "result":I
    const/4 v12, -0x1

    if-eq v5, v12, :cond_c

    .line 239
    const/4 v12, 0x1

    move v13, v12

    .line 241
    .end local v5    # "result":I
    .end local v10    # "o":Ljava/lang/Object;
    :cond_c
    move-object/from16 v5, v20

    goto :goto_4

    .line 242
    .end local v20    # "fieldClass":Ljava/lang/Class;, "Ljava/lang/Class<*>;"
    .local v5, "fieldClass":Ljava/lang/Class;, "Ljava/lang/Class<*>;"
    :cond_d
    move-object/from16 v20, v5

    .end local v5    # "fieldClass":Ljava/lang/Class;, "Ljava/lang/Class<*>;"
    .restart local v20    # "fieldClass":Ljava/lang/Class;, "Ljava/lang/Class<*>;"
    invoke-interface {v1}, Ljava/util/Map;->values()Ljava/util/Collection;

    move-result-object v5

    invoke-interface {v5}, Ljava/util/Collection;->iterator()Ljava/util/Iterator;

    move-result-object v5

    :goto_5
    invoke-interface {v5}, Ljava/util/Iterator;->hasNext()Z

    move-result v6

    if-eqz v6, :cond_f

    invoke-interface {v5}, Ljava/util/Iterator;->next()Ljava/lang/Object;

    move-result-object v6

    .line 243
    .local v6, "o":Ljava/lang/Object;
    const-string v10, "mapValue"

    add-int/lit8 v12, v2, 0x1

    invoke-static {v6, v10, v12, v3, v4}, Ledu/utsa/sefm/heapsnapshot/Snapshot;->checkObjectForPIIRecursive(Ljava/lang/Object;Ljava/lang/String;ILjava/util/List;Ljava/lang/String;)I

    move-result v10

    .line 244
    .local v10, "result":I
    const/4 v12, -0x1

    if-eq v10, v12, :cond_e

    .line 245
    const/4 v13, 0x1

    .line 247
    .end local v6    # "o":Ljava/lang/Object;
    .end local v10    # "result":I
    :cond_e
    goto :goto_5

    .line 248
    :cond_f
    invoke-interface/range {p3 .. p3}, Ljava/util/List;->size()I

    move-result v5

    const/4 v6, 0x1

    sub-int/2addr v5, v6

    invoke-interface {v3, v5}, Ljava/util/List;->remove(I)Ljava/lang/Object;

    .line 249
    nop

    .end local v1    # "mapInstance":Ljava/util/Map;, "Ljava/util/Map<**>;"
    goto :goto_6

    .line 251
    .end local v20    # "fieldClass":Ljava/lang/Class;, "Ljava/lang/Class<*>;"
    .restart local v5    # "fieldClass":Ljava/lang/Class;, "Ljava/lang/Class<*>;"
    :cond_10
    move-object/from16 v20, v5

    .end local v5    # "fieldClass":Ljava/lang/Class;, "Ljava/lang/Class<*>;"
    .restart local v20    # "fieldClass":Ljava/lang/Class;, "Ljava/lang/Class<*>;"
    invoke-virtual {v15}, Ljava/lang/reflect/Field;->getName()Ljava/lang/String;

    move-result-object v1

    add-int/lit8 v5, v2, 0x1

    invoke-static {v0, v1, v5, v3, v4}, Ledu/utsa/sefm/heapsnapshot/Snapshot;->checkObjectForPIIRecursive(Ljava/lang/Object;Ljava/lang/String;ILjava/util/List;Ljava/lang/String;)I

    move-result v1
    :try_end_4
    .catch Ljava/lang/IllegalAccessException; {:try_start_4 .. :try_end_4} :catch_2

    .line 252
    .local v1, "result":I
    const/4 v5, -0x1

    if-eq v1, v5, :cond_11

    .line 253
    const/4 v13, 0x1

    .line 258
    .end local v0    # "fieldInstance":Ljava/lang/Object;
    .end local v1    # "result":I
    .end local v20    # "fieldClass":Ljava/lang/Class;, "Ljava/lang/Class<*>;"
    :cond_11
    :goto_6
    goto :goto_8

    .line 256
    :catch_2
    move-exception v0

    goto :goto_7

    .end local v19    # "objClass":Ljava/lang/Class;, "Ljava/lang/Class<*>;"
    .local v6, "objClass":Ljava/lang/Class;, "Ljava/lang/Class<*>;"
    :catch_3
    move-exception v0

    move-object/from16 v19, v6

    .line 257
    .end local v6    # "objClass":Ljava/lang/Class;, "Ljava/lang/Class<*>;"
    .local v0, "e":Ljava/lang/IllegalAccessException;
    .restart local v19    # "objClass":Ljava/lang/Class;, "Ljava/lang/Class<*>;"
    :goto_7
    new-instance v1, Ljava/lang/RuntimeException;

    invoke-direct {v1, v0}, Ljava/lang/RuntimeException;-><init>(Ljava/lang/Throwable;)V

    throw v1

    .line 191
    .end local v0    # "e":Ljava/lang/IllegalAccessException;
    .end local v19    # "objClass":Ljava/lang/Class;, "Ljava/lang/Class<*>;"
    .restart local v6    # "objClass":Ljava/lang/Class;, "Ljava/lang/Class<*>;"
    :cond_12
    move-object/from16 v19, v6

    .line 167
    .end local v6    # "objClass":Ljava/lang/Class;, "Ljava/lang/Class<*>;"
    .end local v15    # "field":Ljava/lang/reflect/Field;
    .end local v16    # "canAccess":Z
    .restart local v19    # "objClass":Ljava/lang/Class;, "Ljava/lang/Class<*>;"
    :goto_8
    add-int/lit8 v14, v14, 0x1

    move-object/from16 v1, p0

    move-object/from16 v6, v19

    const/4 v5, -0x1

    const/4 v10, 0x1

    goto/16 :goto_0

    .line 263
    .end local v19    # "objClass":Ljava/lang/Class;, "Ljava/lang/Class<*>;"
    .restart local v6    # "objClass":Ljava/lang/Class;, "Ljava/lang/Class<*>;"
    :cond_13
    move-object/from16 v19, v6

    .end local v6    # "objClass":Ljava/lang/Class;, "Ljava/lang/Class<*>;"
    .restart local v19    # "objClass":Ljava/lang/Class;, "Ljava/lang/Class<*>;"
    invoke-interface/range {p3 .. p3}, Ljava/util/List;->size()I

    move-result v0

    const/4 v1, 0x1

    sub-int/2addr v0, v1

    invoke-interface {v3, v0}, Ljava/util/List;->remove(I)Ljava/lang/Object;

    .line 264
    if-eqz v13, :cond_14

    .line 265
    sget v0, Ledu/utsa/sefm/heapsnapshot/Snapshot;->callID:I

    return v0

    .line 268
    :cond_14
    const/4 v1, -0x1

    return v1
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

    .line 30
    new-instance v0, Lorg/json/JSONObject;

    invoke-direct {v0}, Lorg/json/JSONObject;-><init>()V

    .line 32
    .local v0, "resultJson":Lorg/json/JSONObject;
    invoke-virtual {p0}, Ljava/lang/Object;->getClass()Ljava/lang/Class;

    move-result-object v1

    .line 33
    .local v1, "objClass":Ljava/lang/Class;, "Ljava/lang/Class<*>;"
    invoke-virtual {v1}, Ljava/lang/Class;->getName()Ljava/lang/String;

    move-result-object v2

    const-string v3, "class_name"

    invoke-virtual {v0, v3, v2}, Lorg/json/JSONObject;->put(Ljava/lang/String;Ljava/lang/Object;)Lorg/json/JSONObject;

    .line 34
    invoke-virtual {v1}, Ljava/lang/Class;->getModifiers()I

    move-result v2

    const-string v3, "modifiers"

    invoke-virtual {v0, v3, v2}, Lorg/json/JSONObject;->put(Ljava/lang/String;I)Lorg/json/JSONObject;

    .line 36
    invoke-virtual {p0}, Ljava/lang/Object;->hashCode()I

    move-result v2

    const-string v3, "hash_code"

    invoke-virtual {v0, v3, v2}, Lorg/json/JSONObject;->put(Ljava/lang/String;I)Lorg/json/JSONObject;

    .line 39
    invoke-virtual {v1}, Ljava/lang/Class;->getDeclaredFields()[Ljava/lang/reflect/Field;

    move-result-object v2

    .line 44
    .local v2, "fields":[Ljava/lang/reflect/Field;
    array-length v3, v2

    const/4 v4, 0x0

    :goto_0
    if-ge v4, v3, :cond_4

    aget-object v5, v2, v4

    .line 45
    .local v5, "field":Ljava/lang/reflect/Field;
    invoke-virtual {v5}, Ljava/lang/reflect/Field;->getName()Ljava/lang/String;

    move-result-object v6

    .line 49
    .local v6, "fieldName":Ljava/lang/String;
    const/4 v7, 0x1

    invoke-virtual {v5, v7}, Ljava/lang/reflect/Field;->setAccessible(Z)V

    .line 72
    const/4 v8, 0x1

    .line 73
    .local v8, "canAccess":Z
    if-eqz v8, :cond_3

    .line 76
    const/4 v9, 0x0

    .line 77
    .local v9, "child":Ljava/lang/Object;
    :try_start_0
    invoke-virtual {v5}, Ljava/lang/reflect/Field;->getModifiers()I

    move-result v10

    invoke-static {v10}, Ljava/lang/reflect/Modifier;->isStatic(I)Z

    move-result v10

    const/4 v11, 0x0

    if-eqz v10, :cond_0

    .line 78
    invoke-virtual {v5, v11}, Ljava/lang/reflect/Field;->get(Ljava/lang/Object;)Ljava/lang/Object;

    move-result-object v10

    move-object v9, v10

    goto :goto_1

    .line 81
    :cond_0
    invoke-virtual {v5, p0}, Ljava/lang/reflect/Field;->get(Ljava/lang/Object;)Ljava/lang/Object;

    move-result-object v10

    move-object v9, v10

    .line 85
    :goto_1
    if-nez v9, :cond_1

    .line 86
    move-object v7, v11

    check-cast v7, Ljava/util/Map;

    invoke-virtual {v0, v6, v11}, Lorg/json/JSONObject;->put(Ljava/lang/String;Ljava/lang/Object;)Lorg/json/JSONObject;

    goto :goto_2

    .line 89
    :cond_1
    if-le p1, v7, :cond_2

    .line 90
    add-int/lit8 v7, p1, -0x1

    invoke-static {v9, v7}, Ledu/utsa/sefm/heapsnapshot/Snapshot;->takeSnapshot(Ljava/lang/Object;I)Lorg/json/JSONObject;

    move-result-object v7

    invoke-virtual {v0, v6, v7}, Lorg/json/JSONObject;->put(Ljava/lang/String;Ljava/lang/Object;)Lorg/json/JSONObject;

    goto :goto_2

    .line 93
    :cond_2
    const-string v7, "*"

    invoke-virtual {v0, v6, v7}, Lorg/json/JSONObject;->put(Ljava/lang/String;Ljava/lang/Object;)Lorg/json/JSONObject;
    :try_end_0
    .catch Ljava/lang/IllegalAccessException; {:try_start_0 .. :try_end_0} :catch_0

    .line 98
    .end local v9    # "child":Ljava/lang/Object;
    :goto_2
    goto :goto_3

    .line 96
    :catch_0
    move-exception v3

    .line 97
    .local v3, "e":Ljava/lang/IllegalAccessException;
    new-instance v4, Ljava/lang/RuntimeException;

    invoke-direct {v4, v3}, Ljava/lang/RuntimeException;-><init>(Ljava/lang/Throwable;)V

    throw v4

    .line 44
    .end local v3    # "e":Ljava/lang/IllegalAccessException;
    .end local v5    # "field":Ljava/lang/reflect/Field;
    .end local v6    # "fieldName":Ljava/lang/String;
    .end local v8    # "canAccess":Z
    :cond_3
    :goto_3
    add-int/lit8 v4, v4, 0x1

    goto :goto_0

    .line 102
    :cond_4
    return-object v0
.end method
