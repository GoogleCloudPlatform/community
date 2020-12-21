---
title: Modeling entity relationships on App Engine standard environment
description: Learn how to model entity relationships on App Engine standard environment.
author: devlance
tags: App Engine, Datastore
date_published: 2008-06-01
---

Rafe Kaplan | Google

<p style="background-color:#CAFACA;"><i>Contributed by Google employees.</i></p>

Sure, the Getting Started Guide tells you what you need to know in order to fill
properties for a simple App Engine model, but it's going to take more than that
if you want to be able to represent real world concepts in the datastore.
Whether you are new to web application development, or are used to working with
SQL databases, this article is for those people who are ready to take a step
into the next dimension of App Engine data representation.

## Why would I need entity relationships?

Imagine you are building a snazzy new web application that includes an address
book where users can store their contacts. For each contact the user stores, you
want to capture the contact's name, birthday (which they mustn't forget!),
address, telephone number, and company they work for.

When the user wants to add an address, they enter the information into a form
and the form saves the information in a model that looks something like this:

```py
class Contact(db.Model):

    # Basic info.
    name = db.StringProperty()
    birth_day = db.DateProperty()

    # Address info.
    address = db.PostalAddressProperty()

    # Phone info.
    phone_number = db.PhoneNumberProperty()

    # Company info.
    company_title = db.StringProperty()
    company_name = db.StringProperty()
    company_description = db.StringProperty()
    company_address = db.PostalAddressProperty()
```

That's great, your users immediately begin to use their address book and soon
the datastore starts to fill up. Not long after the deployment of your new
application you hear from someone that they are not happy that there is only one
phone number. What if they want to store someone's work telephone number in
addition to their home number? No problem you think, you can just add a work
phone number to your structure. You change your data structure to look more like
this:

    # Phone info.
    phone_number = db.PhoneNumberProperty()
    work_phone_number = db.PhoneNumberProperty()

Update the form with the new field and you are back in business. Soon after
redeploying your application, you get a number of new complaints. When they see
the new phone number field, people start asking for even more fields. Some
people want a fax number field, others want a mobile field. Some people even
want more than one mobile field (boy modern life sure is hectic)! You could add
another field for fax, and another for mobile, maybe two. What about if people
have three mobile phones? What if they have ten? What if someone invents a phone
for a place you've never thought of?

Your model needs to use relationships.

## One to Many

The answer is to allow users to assign as many phone numbers to each of their
contacts as they like. To do this, you need to model the phone numbers in their
own class and have a way of associating many phone numbers to a single Contact.
You can easily model the one to many relationship using ReferenceProperty. Here
is a candidate for this new class:

```py
class Contact(db.Model):

    # Basic info.
    name = db.StringProperty()
    birth_day = db.DateProperty()

    # Address info.
    address = db.PostalAddressProperty()

    # The original phone_number property has been replaced by
    # an implicitly created property called 'phone_numbers'.

    # Company info.
    company_title = db.StringProperty()
    company_name = db.StringProperty()
    company_description = db.StringProperty()
    company_address = db.PostalAddressProperty()

class PhoneNumber(db.Model):
    contact = db.ReferenceProperty(Contact,
                                    collection_name='phone_numbers')
    phone_type = db.StringProperty(
        choices=('home', 'work', 'fax', 'mobile', 'other'))
    number = db.PhoneNumberProperty()
```

The key to making all this work is the `contact` property. By defining it as a
`ReferenceProperty`, you have created a property that can only be assigned
values of type Contact. Every time you define a reference property, it creates
an implicit collection property on the referenced class. By default, this
collection is called `NAME_OF_CLASS_set`. In this case, it would make a property
`Contact.phonenumber_set`. However, it is probably more intuitive to call that
attribute `phone_numbers`. You overrode this default name using the
`collection_name` keyword parameter to `ReferenceProperty`.

Creating the relationship between a contact and one of its phone numbers is easy
to do. Let's say you have a contact named "Scott" who has a home phone and a
mobile phone. You populate his contact info like this:

```py
scott = Contact(name='Scott')
scott.put()
PhoneNumber(contact=scott,
            phone_type='home',
            number='(650) 555 - 2200').put()
PhoneNumber(contact=scott,
            phone_type='mobile',
            number='(650) 555 - 2201').put()
```

Because `ReferenceProperty` creates this special property on `Contact`, it makes
it very easy to retrieve all the phone numbers for a given person. If you wanted
to print all the phone numbers for a given person, you can do it like this:

```py
print 'Content-Type: text/html'
print
for phone in scott.phone_numbers:
    print '%s: %s' % (phone.phone_type, phone.number)
```

This will produce results that look like:

    home: (650) 555 - 2200
    mobile: (650) 555 - 2201

**Note:** The order of the output might be different as by default there is no
ordering in this kind of relationship.

The `phone_numbers` virtual attribute is a `Query` instance, meaning that you
can use it to further narrow down and sort the collection associated with the
`Contact`. For example, if you only want to get the home phone numbers, you can
do this:

```py
scott.phone_numbers.filter('phone_type =', 'home')
```

When Scott loses his phone, it's easy enough to delete that record. Just delete
the PhoneNumber instance and it can no longer be queried for:

```py
scott.phone_numbers.filter('phone_type =', 'home').get().delete()
```

## Many to Many

One thing you would like to do is provide the ability for people to organize
their contacts in to groups. They might make groups like "Friends", "Co-workers"
and "Family". This would allow users to use these groups to perform actions en
masse, such as maybe sending an invitation to all their friends for a
hack-a-thon. Let's define a simple `Group` model like this:

```py
class Group(db.Model):

    name = db.StringProperty()
    description = db.TextProperty()
```

You could make a new `ReferenceProperty` on `Contact` called group. However,
this would allow contacts to be part of only one group at a time. For example,
someone might include some of their co-workers as friends. You need a way to
represent many-to-many relationships.

### List of Keys

One very simple way is to create a list of keys on one side of the relationship:

```py
class Contact(db.Model):
    # ID of user that owns this entry.
    owner = db.StringProperty()

    # Basic info.
    name = db.StringProperty()
    birth_day = db.DateProperty()

    # Address info.
    address = db.PostalAddressProperty()

    # Company info.
    company_title = db.StringProperty()
    company_name = db.StringProperty()
    company_description = db.StringProperty()
    company_address = db.PostalAddressProperty()

    # Group affiliation
    groups = db.ListProperty(db.Key)
```

Adding and removing a user to and from a group means working with a list of
keys:

```py
friends = Group.gql("WHERE name = 'friends'").get()
mary = Contact.gql("WHERE name = 'Mary'").get()
if friends.key() not in mary.groups:
    mary.groups.append(friends.key())
    mary.put()
```

To get all the members of a group, you can execute a simple query. It might help
to add a helper function to the `Group` entity:

```py
class Group(db.Model):
    name = db.StringProperty()
    description = db.TextProperty()

    @property
    def members(self):
        return Contact.gql("WHERE groups = :1", self.key())
```

There are a few limitations to implementing many-to-many relationships this way.
First, you must explicitly retrieve the values on the side of the collection
where the list is stored since all you have available are `Key` objects. Another
more important one is that you want to avoid storing overly large lists of keys
in a `ListProperty`. This means you should place the list on the side of the
relationship which you expect to have fewer values. In the example above, the
`Contact` side was chosen because a single person is not likely to belong to too
many groups, whereas in a large contacts database, a group might contain
hundreds of members.

## Relationship Model

One of your users is a big time saleswoman and knows teams of people in just one
company. She is finding it very tedious to have to enter the same information
about the same company again and again. Couldn't there be a way to specify a
company once and then associate them with each person? If it were that simple,
it would merely be necessary to have a one-to-many relationship between
`Contact` and `Company`, but it's more complicated than that. Some of her
contacts are contractors that work at more than one company and have different
titles in each. What now?

You need a many-to-many relationship that can describe some additional
information about that relationship. To accomplish this, you can use another
`Model` to describe the relationship:

```py
class Contact(db.Model):
    # ID of user that owns this entry.
    owner = db.StringProperty()

    # Basic info.
    name = db.StringProperty()
    birth_day = db.DateProperty()

    # Address info.
    address = db.PostalAddressProperty()

    # The original organization properties have been replaced by
    # an implicitly created property called 'companies'.

    # Group affiliation
    groups = db.ListProperty(db.Key)

class Company(db.Model):
    name = db.StringProperty()
    description = db.StringProperty()
    company_address = db.PostalAddressProperty()

class ContactCompany(db.Model):
    contact = db.ReferenceProperty(Contact,
                                    required=True,
                                    collection_name='companies')
    company = db.ReferenceProperty(Company,
                                    required=True,
                                    collection_name='contacts')
    title = db.StringProperty()
```

Adding someone to a company is done by creating a `ContactCompany` instance:

```py
mary = Contact.gql("name = 'Mary'").get()
google = Company.gql("name = 'Google'").get()
ContactCompany(contact=mary,
                company=google,
                title='Engineer').put()
```

In addition to being able to store information about a relationship, using this
method has the advantage over the list-of-keys method in that you can have large
collections on either side of the relationship. However, you need to be very
careful because traversing the connections of a collection will require more
calls to the datastore. Use this kind of many-to-many relationship only when you
really need to, and do so with care to the performance of your application.

## Conclusion

App Engine allows the creation of easy to use relationships between datastore
entities which can represent real-world things and ideas. Use
`ReferenceProperty` when you need to associate an arbitrary number of repeated
types of information with a single entity. Use key-lists when you need to allow
lots of different objects to share other instances between each other. You will
find that these two approaches will provide you with most of what you need to
create the model behind great applications.

## Related links

* [Life of a Datastore Write](https://cloud.google.com/appengine/articles/life_of_write)
* [Transaction Isolation in App Engine](https://cloud.google.com/appengine/articles/transaction_isolation)
* [How Entities and Indexes are Stored](https://cloud.google.com/appengine/articles/storage_breakdown)
* [Modeling Entity Relationships](https://cloud.google.com/appengine/articles/modeling)
* [Updating Your Model's Schema](https://cloud.google.com/appengine/articles/update_schema)
* [Handling Datastore Errors](https://cloud.google.com/appengine/articles/handling_datastore_errors)
* [Index Selection and Advanced Search](https://cloud.google.com/appengine/articles/indexselection)
