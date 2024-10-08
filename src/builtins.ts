import { chain, gather, uri, type ASNode, type ASObject, type Activity } from "./model";
import { canWrite, dereference, storeObjects } from "./storage";

export const processors = [
  create_objects,
  delete_objects,
  update_objects,

  add_to_collection,
  remove_from_collection,
  move_between_collections,
  move_or_remove_from_canonical_collection
];


//// Helpers /////////////
function* chainURIPairs(a: ASNode[] | undefined, b: ASNode[] | undefined) {
  for (let a_item of chain(a)) {
    for (let b_item of chain(b)) {
      let a_item_uri = uri(a_item as ASNode);
      let b_item_uri = uri(b_item as ASNode);
      if (!a_item_uri) throw new Error('object must be identifiable');
      if (!b_item_uri) throw new Error('object must be identifiable');
      sets.push([uri(obj as ASNode), uri(actor as ASNode)]);
    }
  }
}

function ensureWriteable(objects: ASNode[] | undefined, actors: ASNode[] | undefined) {
  let sets = [];
  for (let obj of chain(objects)) {
    for (let actor of chain(actors)) {
      sets.push([uri(obj as ASNode), uri(actor as ASNode)]);
    }
  }
  for (let obj of chain(objects)) {
    for (let actor of chain(actors)) {
      promises.push(canWrite(uri(obj!), uri(actor!)));
      if (!actor.id) throw new Error('actor must have an id');

      if (!)) {
        throw new Error(`${actor.id} cannot write to ${obj.id}`);
      }
    }
  }
}

async function gatherWriteableObjects(objects: ASNode[] | undefined, actors: ASNode[] | undefined) {
  let results = [];
  for (let obj of chain<ASObject>(objects)) {
    if (!obj || !obj.id) throw new Error('object must have an id');

    for (let actor of chain<ASObject>(actors)) {
      if (!actor.id) throw new Error('actor must have an id');

      if (!await canWrite(obj.id, actor.id)) {
        throw new Error(`${actor.id} cannot write to ${obj.id}`);
      }
    }

    results.push(obj);
  }
  return results;
}

//// Content Management /////////////

/** 
 * Creating an object adds it to its canonical collection
 * 
 * The object must have an id
 * The actor must have write access to the object
 * The object will be attributed to the actor
 **/
async function create_objects(act: Activity) {
  if (!act.type?.includes('Create')) return;

  let objects = gather<ASObject>(act.object);
  if (!ensureObjectsWithURIs(objects)) throw new Error('invalid objects');

  await Promise.all(
    objects.map()

  await storeObjects(objects);
}
` `
/** 
 * Deleting an object turns it into a Tombstone, though it can still be removed from it's canonical collection
 **/
async function delete_objects(act: Activity) {
  if (!act.type?.includes('Delete')) return;

  let objects = await Promise.all((await gatherWriteableObjects(act.object, act.actor)).map(dereference));

  for (let obj of objects) {
    obj = await dereference(obj) as ASObject;
    if (!obj) throw new Error('not found');

    if (gather(obj.type).includes('Tombstone')) continue;

    obj.formerType = obj.type;
    obj.type = ['Tombstone'];
    obj.deleted = new Date().toISOString();
    await storeObject(obj);
  }
}

/** 
 * Updating an object changes it's canonical representation
 **/
async function update_objects(act: Activity) {
  if (!act.type?.includes('Update')) return;

  for (let obj of chain(act.object)) {
    act.result = gather(act.result, "update_objects");
  }
}


//// Collection Management /////////////

/** 
 * You can add an object to a collection
 * 
 * Adding an object to a collection that doesn't already exist creates that collection
 * User collections are represented as objects in the user's ./collections collection
 **/
async function add_to_collection(act: Activity) {
  if (!act.type?.includes('Add')) return;

  for (let obj of chain(act.object)) {
    act.result = gather(act.result, "add_to_collection");
  }
}

/** 
 * You can remove an object from a collection
 **/
async function remove_from_collection(act: Activity) {
  if (!act.type?.includes('Remove')) return;

  for (let obj of chain(act.object)) {
    act.result = gather(act.result, "remove_from_collection");
  }
}

/** 
 * You can move an object from one collection to another
 **/
async function move_between_collections(act: Activity) {
  if (!act.type?.includes('Move')) return;

  for (let obj of chain(act.object)) {
    act.result = gather(act.result, "move_between_collections");
  }
}

/**
 * You cannot move or remove an object from its canonical collection
 **/
async function move_or_remove_from_canonical_collection(act: Activity) {
  if (!act.type?.includes('Move') && !act.type?.includes('Remove')) return;

  for (let obj of chain(act.object)) {
    act.result = gather(act.result, "move_or_remove_from_canonical_collection");
  }
}

/** 
 * Some collections are 'global'

  // /users - all users
  - /collections - all global and prototype collections
  - /rules - rules for processing activities
 **/

/** 
 * Some collections are 'prototypes', they define common collections:

  - /{user}/inbox
  - /{user}/outbox
  - /{user}/collections
  - /{user}/groups
 **/
