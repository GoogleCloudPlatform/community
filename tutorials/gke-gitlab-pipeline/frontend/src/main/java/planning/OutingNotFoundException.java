package planning;

public class OutingNotFoundException extends RuntimeException {

	OutingNotFoundException(Long id) {
		super("Could not find employee " + id);
	}
}
