package opa.elasticsearch;

import org.elasticsearch.index.query.QueryBuilder;
import com.fasterxml.jackson.databind.ObjectMapper;

import java.util.*;

public class Main {
    public static void main(String[] args) {
        String regoPolicy = """
        allowed contains x if {
            some x in data.elastic.posts
            x.author == input.user
            x.age >= input.min_age
        }

        allowed contains x if {
            some x in data.elastic.posts
            x.category == "Tech"
        }

        allowed contains x if {
            some x in data.elastic.posts.comments
            some y in x.comments
            y.author == input.user
        }
        """;

        Map<String, String> inputValues = new HashMap<>();
        inputValues.put("user", "bob");
        inputValues.put("min_age", "25");

        Map<String, Object> opaQuery = OPAQueryExtractor.extractOPAQuery(regoPolicy);
        QueryBuilder esQuery = ESQueryGenerator.generateESQuery(opaQuery, inputValues);

        try {
            ObjectMapper mapper = new ObjectMapper();
            System.out.println("Extracted OPA Query:");
            System.out.println(mapper.writerWithDefaultPrettyPrinter().writeValueAsString(opaQuery));

            System.out.println("\nGenerated Elasticsearch Query:");
            System.out.println(esQuery.toString());
        } catch (Exception e) {
            e.printStackTrace();
        }
    }
}
