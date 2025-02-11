package opa.elasticsearch;

import java.util.*;
import java.util.regex.*;

public class OPAQueryExtractor {
    private static final Pattern RULE_PATTERN = Pattern.compile(
        "some (\\w+) in (data\\.[\\w\\.]+)\\s*\\n?([\\w.]+)\\s*(==|!=|<|<=|>|>=|contains|re_match)\\s*(input\\.\\w+|\"[^\"]+\")"
    );

    public static Map<String, Object> extractOPAQuery(String regoPolicy) {
        Map<String, Object> opaQuery = new HashMap<>();
        List<List<Map<String, String>>> conditionGroups = new ArrayList<>();

        // Split policy into logical rule groups
        String[] ruleBlocks = regoPolicy.split("allowed contains x if \\{");

        for (String block : ruleBlocks) {
            List<Map<String, String>> conditions = new ArrayList<>();
            Matcher matcher = RULE_PATTERN.matcher(block);

            while (matcher.find()) {
                Map<String, String> condition = new HashMap<>();
                String iterator = matcher.group(1);
                String index = matcher.group(2).replace("data.", ""); // Strip "data."
                String field = matcher.group(3).replace(iterator + ".", ""); // Remove iterator prefix
                String operator = matcher.group(4);
                String value = matcher.group(5);

                condition.put("index", index);
                condition.put("field", field);
                condition.put("operator", operator);
                condition.put("value", value);

                conditions.add(condition);
            }

            if (!conditions.isEmpty()) {
                conditionGroups.add(conditions);
            }
        }

        opaQuery.put("conditionGroups", conditionGroups);
        return opaQuery;
    }
}
