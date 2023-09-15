package edu.utsa.sefm.heapsnapshot;

import android.util.Log;

import org.json.JSONException;
import org.json.JSONObject;

import java.util.HashSet;
import java.util.Set;

public class SnapshotTest {
    public static void test() {
        createDataModelAndDump();
    }

    private static void createDataModelAndDump() {
        Set<String> availableCoffee = new HashSet<>();
        availableCoffee.add("Pike's Place Roast");
        availableCoffee.add("Secret");
        availableCoffee.add("Hazelnut");
        Office branford = new Office("Secret",availableCoffee,1,100000,10,true);
        branford.addConferenceRoom("Room A", "Room B", "Room C");
        Office stamford = new Office("Waltham HQ",availableCoffee,2,200000,10,true);
        stamford.addConferenceRoom("2113", "Room 2114");
        Office norwalk = new Office("Norwark",availableCoffee,3,300000,10,true);
        norwalk.addConferenceRoom("A1", "Room B1");

        branford.addEmployee("1",new Person("Bob","Smith",34),1,1,"203-888-5555");
        branford.addEmployee("2",new Person("John","Secret",34),1,2,"203-647-0000");

        stamford.addEmployee("3",new Person("Karen","Kostner",20),1,2,"781-000-0001");


        stamford.addEmployee("4",new Person("Adam","Appleton",55),
                5,5,"781-000-0001");

        norwalk.addEmployee("3",new Person("Lomax","Donner",20),
                1,2,"401-000-0001");
        norwalk.addEmployee("4",new Person("Nick","Secret",55),
                5,5,"401-000-0002");

        branford.addNearbyOffice(stamford);
        branford.addNearbyOffice(norwalk);

        stamford.addNearbyOffice(branford);
        stamford.addNearbyOffice(norwalk);

        norwalk.addNearbyOffice(stamford);

        norwalk.addNearbyOffice(branford);

        norwalk.fireEmployee("4");

//        JSONObject json = null;
//        try {
//            json = Snapshot.takeSnapshot(branford, 3);
//        } catch (JSONException e) {
//            e.printStackTrace();
//        }

        Snapshot.checkObjectForPII(branford, "dunno");

//        JSONObject resultJson = new JSONObject();

//        largeLog("HeapSnapshot", "json: " + json);
//
//        Log.d("HeapSnapshot", "Json printed.");

//            try (PrintWriter writer = new PrintWriter("snapshot.json")) {
//                writer.println(json);
//            }
    }

    public static void methodWithPrimitiveAndObjectArguments(int a, int b, double c, String d, String e) {
        Log.i("Test", "methodWithPrimitiveAndObjectArguments: test function");
    }

}
