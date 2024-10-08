import { expect, test, beforeEach } from "bun:test";
import { ProcessingError, process } from "../src";
import { first, gather, type ASObject } from "../src/model";
import { dereference, loadMemory } from "../src/storage";


const noteHello = {
  'id': '/users/1/notes/1',
  'type': ['Note'],
  'content': ['Hello, world!']
}

const actorTester = {
  id: '/users/1',
  type: ['Person']
}

beforeEach(() => {
  loadMemory({});
});


test("Create a note", async () => {
  let act = await process({
    type: ['Create'],
    actor: [actorTester],
    object: [noteHello]
  }, true);

  expect(act.type).toEqual(['Create']);

  let obj = first(act.object) as ASObject;
  expect(obj.id).toStartWith(actorTester.id);
  expect(obj).toMatchObject(noteHello);

  let saved = await dereference(obj.id!) as ASObject;
  expect(saved).toMatchObject(noteHello);

  let attributedTo = first(saved.attributedTo) as ASObject;
  expect(attributedTo.id).toBe(actorTester.id);
});

test("Can't write fails", async () => {
  let act = await process({
    type: ['Create'],
    actor: [actorTester],
    object: [
      { ...noteHello, 'id': '/sys/notes/1' }
    ]
  });

  expect(act.type).toEqual(['Tombstone']);
  expect(act.deleted).toBeDefined();
  expect((act.result![0] as ProcessingError).summary[0]).toEqual('/users/1 cannot write to /sys/notes/1');
});

test("Delete a note", async () => {
  let act = await process({
    type: ['Delete'],
    actor: [actorTester],
    object: [noteHello]
  }, true);

  let obj = await dereference(noteHello.id) as ASObject;
  expect(obj.type).toEqual(['Tombstone']);
});

test("Update a note", async () => {
  let newContent = 'Hello, tests!';
  let act = await process({
    type: ['Update'],
    actor: [actorTester],
    object: [{ ...noteHello, 'content': [newContent] }]
  }, true);

  expect((dereference(noteHello.id) as any).content[0]).toEqual([newContent]);
});

