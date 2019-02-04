package planning;

import lombok.extern.slf4j.Slf4j;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.boot.CommandLineRunner;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
@Slf4j
public class LoadDatabase {

	Logger log = LoggerFactory.getLogger(LoadDatabase.class);
	
	@Bean
	CommandLineRunner initDatabase(OutingRepository repository) {
		return args -> {
			log.info("Preloading " + repository.save(new Outing("January", "Sledding")));
			log.info("Preloading " + repository.save(new Outing("February", "Tubing")));
			
		};
	}
}
