import type { ASNode, ASObject } from "./model";

const memory = new Map<string, ASObject>();
const settings = {
  storage: 'memory'
}

export function loadMemory(items: Record<string, ASObject>) {
  memory.clear();
  for (let id in items) {
    memory.set(id, items[id]);
  }
}

export async function canWrite(objectId: string, userId: string) {
  return objectId.startsWith(userId + '/');
}

export async function storeObject(obj: ASObject) {
  if (!obj.id) throw new Error('object must have an id');

  if (settings.storage === 'memory') {
    memory.set(obj.id, obj);
  }
}

export async function storeObjects(objects: ASObject[] | undefined) {
  if (objects === undefined) return;

  objects.map(obj => {
    if (!obj.id) throw new Error('object must have an id');
  });

  if (settings.storage === 'memory') {
    objects.map(obj => memory.set(obj.id!, obj));
  }
}

export async function dereference(obj: ASNode | undefined) {
  if (!obj) return undefined;

  if (typeof obj === 'string') {
    return memory.get(obj);
  } else {
    return memory.get(obj.id!);
  }
}
