import org.apache.beam.runners.dataflow.options.DataflowPipelineOptions;
import org.apache.beam.sdk.options.Default;
import org.apache.beam.sdk.options.Description;
import org.apache.beam.sdk.options.ValueProvider;

public interface DemoPipelineOptions extends DataflowPipelineOptions {
    @Description("Subscription name")
    @Default.String("demo_subscription")
    ValueProvider<String> getSubscription();
    void setSubscription(ValueProvider<String> subscription);
}
