import org.apache.beam.sdk.Pipeline;
import org.apache.beam.sdk.options.PipelineOptionsFactory;

public class DataflowDemoPipeline {
    public static void main(String[] args){

        // Register Options class for our pipeline with the factory
        PipelineOptionsFactory.register(DemoPipelineOptions.class);

        DemoPipelineOptions options = PipelineOptionsFactory.fromArgs(args)
                .withValidation()
                .as(DemoPipelineOptions.class);

        Pipeline p = Pipeline.create(options);

        p.run();
    }
}

