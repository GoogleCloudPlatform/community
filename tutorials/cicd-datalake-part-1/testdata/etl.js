function transform(line) {
var values = line.split(',');

var obj = new Object();
obj.card_type_full_name = values[0];
obj.issuing_bank = values[1];
obj.card_number = values[2];
obj.card_holders_name = values[3];
obj.cvvcvv2 = values[4];
obj.issue_date = values[5];
obj.expiry_date = values[6];
obj.billing_date = values[7];
obj.card_pin = values[8];
obj.credit_limit = values[9];
obj.card_type_code = values[10];
var jsonString = JSON.stringify(obj);

return jsonString;
}