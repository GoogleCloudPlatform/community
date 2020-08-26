package com.google.example;

import io.micrometer.core.instrument.MeterRegistry;
import io.micronaut.configuration.metrics.aggregator.MeterRegistryConfigurer;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import javax.inject.Singleton;
import java.util.Optional;

@Singleton
public class ApplicationMeterRegistryConfigurer implements MeterRegistryConfigurer {

    private final Logger logger = LoggerFactory.getLogger(ApplicationMeterRegistryConfigurer.class);

    @Override
    public void configure(MeterRegistry meterRegistry) {
        String instanceId = Optional.ofNullable(System.getenv("HOSTNAME")).orElse("localhost");
        logger.info("Publishing metrics for pod " + instanceId);
        meterRegistry.config().commonTags("instance_id", instanceId);
    }

    @Override
    public boolean supports(MeterRegistry meterRegistry) {
        return true;
    }
}
