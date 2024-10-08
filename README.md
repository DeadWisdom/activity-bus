
# Features

- Create, Read, Update, Delete - Objects, within their canonical collection
- Add, Move, Remove - Objects in a collection
- Post activities to an outbox

# Built-in Rules

### Content Management

- Creating an object adds it to its canonical collection
- Deleting an object turns it into a Tombstone, though it can still be removed from it's canonical collection
- Updating an object changes it's canonical representation

### Collection Management

- You can add an object to a collection
- You can remove an object from a collection
- You can move an object from one collection to another
- You cannot move or remove an object from its canonical collection
- Adding an object to a collection that doesn't already exist creates that collection
- User collections are represented as objects in the user's ./collections collection

- Some collections are 'global'

  - /users - all users
  - /collections - all global and prototype collections
  - /rules - rules for processing activities

- Some collections are 'prototypes', they define common collections:

  - /{user}/inbox
  - /{user}/outbox
  - /{user}/collections
  - /{user}/groups

### Security

- Modifying objects cannot be done unless the user is part of the "attributedTo" set, or an object
  up the hierarchy, or has a matching group entry
- Reading is similarly guarded by "attributedTo" or "audience"
- Collection activities (add, move, remove) likewise check the collection's object

### Activities

- An actor can add activities to their outbox which will then be processed
- Processed activities are run against all rules
- Activities can fail, in which case they are turned into a Tombstone

### Agents
