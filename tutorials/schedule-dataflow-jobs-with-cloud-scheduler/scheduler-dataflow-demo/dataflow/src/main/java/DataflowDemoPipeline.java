import org.apache.beam.sdk.Pipeline;
import org.apache.beam.sdk.options.PipelineOptionsFactory;
import org.apache.beam.sdk.transforms.Create;
import org.apache.beam.sdk.transforms.DoFn;
import org.apache.beam.sdk.transforms.ParDo;
import org.apache.beam.sdk.values.PDone;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.Arrays;
import java.util.List;

public class DataflowDemoPipeline {
    private static final Logger Log = LoggerFactory.getLogger(DataflowDemoPipeline.class);

    public static void main(String[] args) {
        // Register Options class for our pipeline with the factory
        PipelineOptionsFactory.register(DemoPipelineOptions.class);

        DemoPipelineOptions options = PipelineOptionsFactory.fromArgs(args)
                .withValidation()
                .as(DemoPipelineOptions.class);

        Pipeline p = Pipeline.create(options);

        String[] numbers = new String[]{"one", "two", "three"};
        List<String> input = Arrays.asList(numbers);
        p.apply("dummy input", Create.of(input)).
                apply("dummy transformation", ParDo.of(
                        new DoFn<String, String>() {
                            @ProcessElement
                            public void processElement(ProcessContext context) {
                                String elem = context.element();
                                Log.info("Process element: " + elem);
                                context.output(elem);
                            }
                        }
                ));
        PDone.in(p);
        p.run();
    }
}

