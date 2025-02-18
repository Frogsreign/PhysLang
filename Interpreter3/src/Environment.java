import java.util.HashMap;
import java.util.Map;

public class Environment {
    Environment enclosing = null;

    public Environment() {
    }

    public Environment(Environment enclosing) {
        this.enclosing = enclosing;
    }

    private Map<String, Object> variables = new HashMap<>();

    // Define - Create a variable
    void define(String name, Object value) {
        variables.put(name, value);
    }

    Object get(String name) {
        // TODO: Return variable if it exists in our current environment, otherwise, check enclosing, otherwise,
        //  return null (it does not exist)
        if (variables.get(name) != null) { // check the current level environment variable hashmap
            return variables.get(name);
        } else if (this.enclosing.get(name) != null) { // use the enclosing environment's own get method to access that hashmap
            return this.enclosing.get(name);
        }
        return null; // what is this variable? so sudden and new? it's not real!
    }

    // Assign - Replace the value of an existing variable
    void assign(Token name, Object value) {
        // TODO: If the variable exists, then we can assign, otherwise we have an error
        if (get(name.text) == null) System.exit(ErrorCode.INTERPRET_ERROR);

        // TODO: If we don't have it in our current environment, try assigning in the enclosing environment
        if (variables.get(name.text) != null) {
            variables.replace(name.text, value);
            return;
        }
        else if (this.enclosing.get(name.text) != null) {
            this.enclosing.assign(name, value);
            return;
        }

        // Exit on error if we get this far since the variable is undefined
        System.err.println("Undefined variable: " + name.text);
        System.exit(ErrorCode.INTERPRET_ERROR);
    }
}
