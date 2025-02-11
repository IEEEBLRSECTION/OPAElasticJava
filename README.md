**OPAElasticJava 🚀**
**Convert Open Policy Agent (OPA) Rego Policies into Elasticsearch Queries**  

🔹 **Supports:**  
✅ **Nested Queries** (e.g., `data.elastic.posts.comments.author`)  
✅ **AND/OR Logic** for complex conditions  
✅ **Various Operators** (`==`, `!=`, <, >, contains, re_match)  

---

## **🛠 Setup & Installation**  

### **1️⃣ Clone the Repository**  
```sh
git clone https://github.com/IEEEBLRSECTION/OPAElasticJava.git
cd OPAElasticJava
```

### **2️⃣ Add Elasticsearch Dependency**  
If using **Maven**, add this to your `pom.xml`:  
```xml
<dependencies>
    <dependency>
        <groupId>org.elasticsearch</groupId>
        <artifactId>elasticsearch</artifactId>
        <version>7.10.2</version>
    </dependency>
</dependencies>
```

### **3️⃣ Compile and Run**  
```sh
mvn compile exec:java -Dexec.mainClass="opa.elasticsearch.Main"
```

---

## **🚀 Usage**  

### **Example OPA Rego Policy**
```rego
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
```

---

## **💡 How It Works?**  

1️⃣ **Extracts OPA Query Conditions**  
```json
{
  "conditionGroups": [
    [
      { "index": "elastic.posts", "field": "author", "operator": "==", "value": "input.user" },
      { "index": "elastic.posts", "field": "age", "operator": ">=", "value": "input.min_age" }
    ],
    [
      { "index": "elastic.posts", "field": "category", "operator": "==", "value": "\"Tech\"" }
    ],
    [
      { "index": "elastic.posts.comments", "field": "author", "operator": "==", "value": "input.user" }
    ]
  ]
}
```

2️⃣ **Generates Equivalent Elasticsearch Query**  
```json
{
  "bool": {
    "should": [
      {
        "bool": {
          "must": [
            { "term": { "author": "bob" } },
            { "range": { "age": { "gte": "25" } } }
          ]
        }
      },
      {
        "bool": {
          "must": [
            { "term": { "category": "Tech" } }
          ]
        }
      },
      {
        "nested": {
          "path": "elastic.posts.comments",
          "query": {
            "term": { "author": "bob" }
          }
        }
      }
    ]
  }
}
```

---

## **📜 Features**  
✅ **Supports Term, Range, and Regex Queries**  
✅ **Handles AND / OR Conditions Automatically**  
✅ **Nested Query Support for Deeply Nested Documents**  
✅ **Customizable Operators**  

---

## **📌 Contribution**  
🔹 Fork the repo  
🔹 Create a new branch  
🔹 Make your changes & test  
🔹 Submit a pull request  
