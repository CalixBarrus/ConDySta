package edu.utsa.sefm.heapsnapshot;

import android.util.Log;

import androidx.annotation.NonNull;

import org.json.JSONException;
import org.json.JSONObject;
//import org.openjdk.jol.vm.VM;

import java.io.UnsupportedEncodingException;
import java.lang.reflect.Field;
//import java.lang.reflect.InaccessibleObjectException;
import java.lang.reflect.Modifier;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collection;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

public class Snapshot {
    // private static final int INSPECTION_DEPTH = 3;
    // private static final int INSPECTION_DEPTH = 2;
    private static final int INSPECTION_DEPTH = 1;
    private static final boolean CHECK_COLLECTION_ELEMENTS = false;
    private static final boolean CHECK_MAP_ELEMENTS = false;

    // Personally identifiable information known a priori
    // mint_mobile_SIM_id, nexus_6_IMEI, serial #, advertising ID, Wifi Mac Address, Bluetooth mac address, google account email, google account password
    private static final List<String> PII = Arrays.asList("8901240197155182897", "355458061189396", "ZX1H22KHQK", "b91481e8-4bfc-47ce-82b6-728c3f6bff60", "f8:cf:c5:d1:02:e8", "f8:cf:c5:d1:02:e7", "tester.sefm@gmail.com", "Class-Deliver-Put-Earn-5", 
        // Unique-ish Strings observed from "Ljava/util/Locale; toString", "Landroid/provider/Settings$Secure; getString", "Landroid/net/nsd/NsdServiceInfo; getServiceName", respectively.
        "en_US", "3a15cc3d742be836", "Q2hhbm5lbF8wMA:OhXMPXQr6DY:");

    private static final String HARNESSED_PII_PATTERN = "\\*\\*\\*\\d{12}\\*\\*\\*";

    private static final List<Class<?>> EXCLUDED_CLASSES = Arrays.asList(Integer.class, Long.class, Double.class, Boolean.class);
    private static final String TAG = "Snapshot";
    private static final String DEBUG_TAG = "Snap-Debug";
    // This can only be accessed/updated in synchronized blocks
    private static int callId = 0;
    // TODO: Should this be a synchronized HashMap? I think i can get away without it, since it's keyed by threadId
    private static Map<Long, Boolean> isThreadCheckingObjectMap = new HashMap<>();

    public static JSONObject takeSnapshot(Object obj, int inspectionDepth) throws JSONException {
        JSONObject resultJson = new JSONObject();

        Class<?> objClass = obj.getClass();
        resultJson.put("class_name", objClass.getName());
        resultJson.put("modifiers", objClass.getModifiers());
//        resultJson.put("current_address", VM.current().addressOf(obj));
        resultJson.put("hash_code", obj.hashCode());
//        System.out.println(objClass.toString());

        Field[] fields = objClass.getDeclaredFields();

        // No String Class cache

        for (Field field :
                fields) {
            String fieldName = field.getName();
//            System.out.println(field.toString());

            // Dangerous command!! Prone to causing Exceptions!
            field.setAccessible(true);
//            try {
//                field.setAccessible(true);
//            }
//            catch (InaccessibleObjectException e) {
//                // Error message looks like:
//                // Unable to make field private static boolean jdk.internal.reflect.ReflectionFactory.initted accessible: module java.base does not "opens jdk.internal.reflect" to unnamed module @1d251891
//                Pattern pattern = Pattern.compile("opens ([\\w.]+)", Pattern.CASE_INSENSITIVE);
//                Matcher matcher = pattern.matcher(e.getMessage());
//                if (matcher.find()) {
//                    String closedPackageName = matcher.group(1);
//                    resultJson.put(fieldName, String.format("Closed Package %s in Field %s", closedPackageName, field));
//                    System.out.printf("Closed Package in obj Class %s, Field %s. Package name is %s%n",
//                            objClass, field, closedPackageName);
//                }
//                else {
//                    System.out.println("Some unrecognized Closed Package! " + e.getMessage());
//                }
//            }
            // Danger!

//            boolean canAccess = (Modifier.isStatic(field.getModifiers()) && field.canAccess(null))
//                    || (!Modifier.isStatic(field.getModifiers()) && field.canAccess(obj));
            boolean canAccess = true;
            if (canAccess) {
                try {

                    Object child = null;
                    if (Modifier.isStatic(field.getModifiers())) {
                        child = field.get(null);
                    }
                    else {
                        child = field.get(obj);
                    }

                    // TODO: save result as value
                    if (child == null) {
                        resultJson.put(fieldName, (Map<?, ?>) null);
                    }
                    else {
                        if (inspectionDepth > 1) {
                            resultJson.put(fieldName, takeSnapshot(child, inspectionDepth-1));
                        }
                        else {
                            resultJson.put(fieldName, "*");
                        }
                    }
                } catch (IllegalAccessException e) {
                    throw new RuntimeException(e);
                }
            }
            // Failure to access already recorded in the InaccessibleObjectException catch block
        }
        return resultJson;
    }

    public static int checkObjectForPII(Object instance, String invocationDescription) {
        /*
        Recursively traverse the provided instance checking fields and subfields for PII.

        Returns an ID number associated with the logged message or -1 if no PII was found.
         */

        // This needs to be thread safe
        int localCallId = 0;
        synchronized (Snapshot.class) {
            callId += 1;
            localCallId = callId;
        }


        // How often does this function get called? 
        int div = 100;
        if (localCallId % div == 0) {
            Log.d(DEBUG_TAG, "Calls to checkObjectForPII :" + localCallId);
        }

        // This needs to be done in a thread safe way
        // TODO: can i get away without using a synchronized map? And without using synchronized blocks? 
        //      I think so. Intuition dictates that keying in using the ThreadId *shouldn't* lead to any bad behavior.
        // start thread safe
        Long threadId = Thread.currentThread().getId();
        if (!Snapshot.isThreadCheckingObjectMap.containsKey(threadId)) {
            Snapshot.isThreadCheckingObjectMap.put(threadId, false);
            // Debug
            Log.e(DEBUG_TAG, "Creating entry in thread map, Thread ID is " + threadId); 
            // End Debug
        }


        Boolean isCheckingObject = Snapshot.isThreadCheckingObjectMap.get(threadId);

        // // Debug
        // Log.e(DEBUG_TAG, "Checking thread map, Thread ID is " + threadId + " and result is " + isCheckingObject); 
        // // End Debug
        
        // end thread safe

        // If for some reason the instrumentation code is triggered while we are already checking an object, don't enter an infinite recursion.
        if (isCheckingObject) {
            Log.d(DEBUG_TAG, "Avoided Infinite recursion at invocation: " + invocationDescription);

            // TODO: add stacktrace info here so we can what in the instr code is causing the recursion; its probably instance.getClass(), and 
            
            // Debug
            Log.e(DEBUG_TAG, "Thread ID is " + threadId + ", Printing stacktrace:"); 
            (new Exception(DEBUG_TAG)).printStackTrace(); // This will print to stderr
            // End Debug

            return -1;
        }

        int currentInspectionDepth = 0;
        List<FieldInfo> accessPath = new ArrayList<>();

        if (instance == null) {
            return -1;
        }                
                
        // start thread safe
        Snapshot.isThreadCheckingObjectMap.put(threadId, true);
        // end thread safe
        // // Debug
        // Log.e(DEBUG_TAG, "Setting entry in thread map to true, Thread ID is " + threadId); 
        // // End Debug
        

        int result = checkObjectForPIIRecursive(instance, ".", currentInspectionDepth, accessPath, invocationDescription, localCallId);

        // start thread safe
        Snapshot.isThreadCheckingObjectMap.put(threadId, false);
        // end thread safe
        // // Debug
        // Log.e(DEBUG_TAG, "Setting entry in thread map to false, Thread ID is " + threadId); 
        // // End Debug

        return result;

        // Can't get the address of an object in Dalvik using this function
//        resultJson.put("current_address", VM.current().addressOf(obj));
    }

    private static int checkObjectForPIIRecursive(Object instance,
                                                  String instanceName,
                                                  int curDepth,
                                                  List<FieldInfo> accessPath,
                                                  String invocationDescription,
                                                  int localCallID) {
        if (instance == null) {
            return -1;
        }
        Class<?> objClass = instance.getClass();
        accessPath.add(new FieldInfo(objClass.getName(), instanceName));
        boolean childFoundLeak = false;

//         Debug
//        Log.d(TAG, "checkObjectForPIIRecursive: inspecting object " + (new FieldInfo(objClass.getName(), instanceName)));
//         End Debug

        // Is the instance a tainted String?
        if (objClass.equals(String.class)) {
            // Access contents of object
            String stringInstance = (String) instance;

            // Check against PII
            for (String piiString: PII) {
                if (stringInstance.contains(piiString)) {
                    // Tainted String found!
                    Log.d(TAG, invocationDescription + ";" + accessPath + ";" + stringInstance);
                    Log.d(DEBUG_TAG, "String matched against: " + piiString);
                    childFoundLeak = true;
                }
            }

            // Check against regex pattern 
            Pattern pattern = Pattern.compile(HARNESSED_PII_PATTERN);
            if (pattern.matcher(stringInstance).find()) {
                // Tainted String found!
                Log.d(TAG, invocationDescription + ";" + accessPath + ";" + stringInstance);
                Log.d(DEBUG_TAG, "String matched against pattern: " + HARNESSED_PII_PATTERN);
                childFoundLeak = true;
            }

            // if (stringInstance.contains("***")) {
            //     // Tainted String found!
            //     Log.d(DEBUG_TAG, invocationDescription + ";" + accessPath + ";" + stringInstance);
            //     Log.d(DEBUG_TAG, "String matched against: " + "***");
            //     Log.d(DEBUG_TAG, "Result of RE matcher: " + pattern.matcher(stringInstance));
            //     Log.d(DEBUG_TAG, "Result of RE code find: " + pattern.matcher(stringInstance).find());
            // }

        }

        // Halt recursion if curDepth has the max depth
        if (!(curDepth < INSPECTION_DEPTH)) {
            accessPath.remove(accessPath.size()-1);
            if (childFoundLeak) {
                return localCallID;
            }
            else {
                return -1;
            }
        }

        // Does the instance have any children (that we should check?)
        // Are any of it's children a tainted String?
        Field[] fields = objClass.getDeclaredFields();
        for (Field field : fields) {


            boolean canAccess = false;
            try {
                // Dangerous command!! Prone to causing Exceptions!
                field.setAccessible(true);
                canAccess = true;
            }
            catch (SecurityException e) {
                // Error message looks like:
                // Unable to make field private static boolean jdk.internal.reflect.ReflectionFactory.initted accessible: module java.base does not "opens jdk.internal.reflect" to unnamed module @1d251891
                Pattern pattern = Pattern.compile("opens ([\\w.]+)", Pattern.CASE_INSENSITIVE);
                Matcher matcher = pattern.matcher(e.getMessage());
                if (matcher.find()) {
                    String closedPackageName = matcher.group(1);
                    Log.d("Snapshot", String.format("Closed Package %s in Field %s", closedPackageName, field));
                }
                else {
                    Log.d("Snapshot", "Some unrecognized Closed Package! " + e.getMessage());
                }
            }

            if (canAccess) {
                try {
                    Object fieldInstance = null;
                    if (Modifier.isStatic(field.getModifiers())) {
                        fieldInstance = field.get(null);
                    }
                    else {
                        fieldInstance = field.get(instance);
                    }

                    if (fieldInstance == null) {
                        continue;
                    }

                    Class<?> fieldClass = fieldInstance.getClass();

                    // Debug
//                    Log.d(TAG, "checkObjectForPIIRecursive: " + fieldClass.getName() + ", " + field.getName());
//                    Log.d(TAG, "checkObjectForPIIRecursive: " + Collection.class.isAssignableFrom(fieldClass));
                    // End Debug

                    // Shall we recur on this field?
                    if (fieldClass.isPrimitive()) {
                        // Primitives cannot contain strings
                        continue;
                    }
                    else if (EXCLUDED_CLASSES.contains(fieldClass)) {
                        // Skip certain well known classes
                        continue;
                    }
                    else if (Collection.class.isAssignableFrom(fieldClass)) {
                        if (CHECK_COLLECTION_ELEMENTS) {
                            Collection<?> collectionInstance = (Collection<?>) fieldInstance;
                            accessPath.add(new FieldInfo(fieldClass.getName(), field.getName()));

                            for (Object o : collectionInstance) {
                                int result = checkObjectForPIIRecursive(o, "collectionElement", curDepth+1, accessPath, invocationDescription, localCallID);
                                if (result != -1) {
                                    childFoundLeak = true;
                                }
                            }
                            accessPath.remove(accessPath.size()-1);
                        }
                        else {
                            continue;
                        }
                    }
                    else if (Map.class.isAssignableFrom(fieldClass)) {
                        if (CHECK_MAP_ELEMENTS) {
                        Map<?, ?> mapInstance = (Map<?, ?>) fieldInstance;
                        accessPath.add(new FieldInfo(fieldClass.getName(), field.getName()));
                        for (Object o : mapInstance.keySet()) {
                            int result = checkObjectForPIIRecursive(o, "mapKey", curDepth+1, accessPath, invocationDescription, localCallID);
                            if (result != -1) {
                                childFoundLeak = true;
                            }
                        }
                        for (Object o : mapInstance.values()) {
                            int result = checkObjectForPIIRecursive(o, "mapValue", curDepth+1, accessPath, invocationDescription, localCallID);
                            if (result != -1) {
                                childFoundLeak = true;
                            }
                        }
                        accessPath.remove(accessPath.size()-1);
                        }
                        else {
                            continue;
                        }

                    }
                    else {
                        int result = checkObjectForPIIRecursive(fieldInstance, field.getName(), curDepth+1, accessPath, invocationDescription, localCallID);
                        if (result != -1) {
                            childFoundLeak = true;
                        }
                    }
                } catch (IllegalAccessException e) {
                    throw new RuntimeException(e);
                }
            }
        }

        // Pop off most recent accessPath entry
        accessPath.remove(accessPath.size()-1);
        if (childFoundLeak) {
            return localCallID;
        }
        else {
            return -1;
        }
    }

    public static void logHarnessedSource(Object original_return_value, String message) {
        String HARNESSED_SOURCE_TAG = "HarnessedSource";
        
        // Start debug
        Log.d("DEBUGGG", "Method was called " + message);
        // end debug

        if (original_return_value == null) {
            Log.d(HARNESSED_SOURCE_TAG, message + ";null");    
            return;
        }
        Class<?> objClass = original_return_value.getClass();
        if (!objClass.equals(String.class)) {

            Log.d(HARNESSED_SOURCE_TAG, message + ";unknown");    
            return;
        }
        
        String original_return_value_cast = (String) original_return_value;

        // // Check if string can be converted to UTF-8
        // // TODO: this check is not working; it's being handled in Python
        // boolean isUtf8Encoding = true;
        // try 
        // {
        //     byte[] bytes = null;
        //     bytes = original_return_value_cast.getBytes("UTF-8");
        // } 
        // catch (UnsupportedEncodingException e)
        // {
        //     isUtf8Encoding = false;
        //     Log.d(HARNESSED_SOURCE_TAG + "_DEBUG", "Encountered String not compatible with UTF-8");    
        //     Log.d(HARNESSED_SOURCE_TAG, message + ";");    
        //     return;
        // }

        // if  (isUtf8Encoding) {
        Log.d(HARNESSED_SOURCE_TAG, message + ";" + original_return_value_cast);    
        // }
        
    
    }

    private static class FieldInfo {
        public final String fieldClassName;
        public final String fieldName;

        public FieldInfo(String fieldClassName, String fieldName) {
            this.fieldClassName = fieldClassName;
            this.fieldName = fieldName;
        }

        @NonNull
        @Override
        public String toString() {
            return "<" + fieldClassName + " " + fieldName + ">";
        }
    }

    public static void largeLog(String tag, String content) {
        if (content.length() > 4000) {
            Log.d(tag, content.substring(0, 4000));
            largeLog(tag, content.substring(4000));
        } else {
            Log.d(tag, content);
        }
    }


}
