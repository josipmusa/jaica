
import random

def generate_general_java_snippets(n_samples):
    """
    Generate diverse small Java snippets for training.
    All snippets are labeled 'java'.
    """
    snippets = []

    class_names = ["Test", "Calculator", "LoopExample", "MyClass", "Example"]
    var_names = ["x", "y", "sum", "total", "count", "result", "i", "j"]
    method_names = ["add", "multiply", "compute", "process", "calculate", "run"]
    loop_limits = [5, 10, 20]

    for _ in range(n_samples):
        choice = random.randint(0, 4)

        if choice == 0:
            # Simple main with for-loop
            class_name = random.choice(class_names)
            var_name = random.choice(var_names)
            limit = random.choice(loop_limits)
            snippet = f"""public class {class_name} {{
    public static void main(String[] args) {{
        int {var_name} = 0;
        for (int i = 0; i < {limit}; i++) {{
            {var_name} += i;
        }}
        System.out.println({var_name});
    }}
}}"""
        elif choice == 1:
            # Small function class
            class_name = random.choice(class_names)
            method_name = random.choice(method_names)
            var1, var2 = random.sample(var_names, 2)
            snippet = f"""public class {class_name} {{
    public int {method_name}(int {var1}, int {var2}) {{
        return {var1} + {var2};
    }}
}}"""
        elif choice == 2:
            # If/else example
            class_name = random.choice(class_names)
            var_name = random.choice(var_names)
            snippet = f"""public class {class_name} {{
    public static void main(String[] args) {{
        int {var_name} = {random.randint(0, 10)};
        if ({var_name} % 2 == 0) {{
            System.out.println("Even");
        }} else {{
            System.out.println("Odd");
        }}
    }}
}}"""
        elif choice == 3:
            # Array iteration
            class_name = random.choice(class_names)
            var_name = random.choice(var_names)
            snippet = f"""public class {class_name} {{
    public static void main(String[] args) {{
        int[] arr = {{1,2,3,4,5}};
        for (int {var_name} : arr) {{
            System.out.println({var_name});
        }}
    }}
}}"""
        else:
            # Nested loops
            class_name = random.choice(class_names)
            snippet = f"""public class {class_name} {{
    public static void main(String[] args) {{
        for (int i=0; i<3; i++) {{
            for (int j=0; j<2; j++) {{
                System.out.println(i*j);
            }}
        }}
    }}
}}"""

        snippets.append((snippet, "java"))

    return snippets


def generate_spring_boot_snippets(n_samples):
    """
    Generate small Spring Boot snippets commonly seen in modern apps.
    All snippets are labeled 'java'.
    """
    snippets = []

    controller_names = ["UserController", "ProductController", "OrderController"]
    service_names = ["UserService", "ProductService", "OrderService"]
    repo_names = ["UserRepository", "ProductRepository", "OrderRepository"]
    entity_names = ["User", "Product", "Order"]

    for _ in range(n_samples):
        choice = random.randint(0, 4)

        if choice == 0:
            # Simple RestController with GET mapping
            controller = random.choice(controller_names)
            entity = random.choice(entity_names)
            snippet = f"""@RestController
@RequestMapping("/api/{entity.lower()}s")
public class {controller} {{

    @Autowired
    private {entity}Service {entity.lower()}Service;

    @GetMapping
    public List<{entity}> getAll{entity}s() {{
        return {entity.lower()}Service.getAll{entity}s();
    }}
}}"""
        elif choice == 1:
            # Service with Autowired repository
            service = random.choice(service_names)
            repo = random.choice(repo_names)
            entity = random.choice(entity_names)
            snippet = f"""@Service
public class {service} {{

    @Autowired
    private {repo} {repo[0].lower() + repo[1:]};

    public List<{entity}> getAll{entity}s() {{
        return {repo[0].lower() + repo[1:]}.findAll();
    }}
}}"""
        elif choice == 2:
            # Repository interface
            repo = random.choice(repo_names)
            entity = random.choice(entity_names)
            snippet = f"""@Repository
public interface {repo} extends JpaRepository<{entity}, Long> {{
}}"""
        elif choice == 3:
            # Configuration class with Bean
            snippet = f"""@Configuration
public class AppConfig {{

    @Bean
    public String exampleBean() {{
        return "example";
    }}
}}"""
        else:
            # Small RestController with POST mapping
            controller = random.choice(controller_names)
            entity = random.choice(entity_names)
            snippet = f"""@RestController
@RequestMapping("/api/{entity.lower()}s")
public class {controller} {{

    @PostMapping
    public {entity} create{entity}(@RequestBody {entity} {entity.lower()}) {{
        // Imagine saving to service
        return {entity.lower()};
    }}
}}"""

        snippets.append((snippet, "java"))

    return snippets
