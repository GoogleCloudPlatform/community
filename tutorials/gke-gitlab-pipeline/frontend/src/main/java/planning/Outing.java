package planning;

import lombok.Data;

import javax.persistence.Entity;
import javax.persistence.GeneratedValue;
import javax.persistence.Id;


@Data
@Entity
public class Outing {
	
	private @Id @GeneratedValue Long id;
	private String month;
	private String event;
	
	Outing() {}
	
	Outing(String name, String role) {
		this.month = name;
		this.event = role;
	}

	public String getName() {
		return month;
	}

	public String getRole() {
		return event;
	}

	public void setName(String name) {
		this.month = name;
	}

	public void setRole(String role) {
		this.event = role;
	}

	public void setId(Long id) {
		this.id = id;
	}

}
