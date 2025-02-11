package opa.elasticsearch;

import org.elasticsearch.index.query.*;
import java.util.*;

public class ESQueryGenerator {
    public static QueryBuilder generateESQuery(Map<String, Object> opaQuery, Map<String, String> inputValues) {
        BoolQueryBuilder boolQuery = QueryBuilders.boolQuery();
        List<List<Map<String, String>>> conditionGroups = (List<List<Map<String, String>>>) opaQuery.get("conditionGroups");

        for (List<Map<String, String>> group : conditionGroups) {
            BoolQueryBuilder groupQuery = QueryBuilders.boolQuery();
            
            for (Map<String, String> condition : group) {
                String field = condition.get("field");
                String index = condition.get("index");
                String operator = condition.get("operator");
                String value = condition.get("value");

                // Replace input reference with actual value
                if (value.startsWith("input.")) {
                    value = inputValues.get(value.replace("input.", ""));
                } else {
                    value = value.replace("\"", "");
                }

                QueryBuilder subQuery = getQueryForOperator(field, operator, value);

                // Handle Nested Queries
                if (index.contains(".")) {
                    groupQuery.must(QueryBuilders.nestedQuery(index, subQuery, ScoreMode.Avg));
                } else {
                    groupQuery.must(subQuery);
                }
            }

            boolQuery.should(groupQuery); // OR condition for separate rule blocks
        }

        return boolQuery;
    }

    private static QueryBuilder getQueryForOperator(String field, String operator, String value) {
        switch (operator) {
            case "==": return QueryBuilders.termQuery(field, value);
            case "!=": return QueryBuilders.boolQuery().mustNot(QueryBuilders.termQuery(field, value));
            case "<": return QueryBuilders.rangeQuery(field).lt(value);
            case "<=": return QueryBuilders.rangeQuery(field).lte(value);
            case ">": return QueryBuilders.rangeQuery(field).gt(value);
            case ">=": return QueryBuilders.rangeQuery(field).gte(value);
            case "contains": return QueryBuilders.matchQuery(field, value);
            case "re_match": return QueryBuilders.regexpQuery(field, value);
            default: throw new IllegalArgumentException("Unsupported operator: " + operator);
        }
    }
}
