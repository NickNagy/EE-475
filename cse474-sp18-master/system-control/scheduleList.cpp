#include "scheduleList.h"
#include "tasks.h"

void ScheduleList::insertTask(TCB* node) {
  if (nullptr == head) {
    this->head = node;
    this->tail = node;
  } else {
    this->tail->next = node;
    node->prev = this->tail;
    this->tail = node;
  }
  return;
}

void ScheduleList::deleteTask(TCB* node) {
  if (nullptr == head) {
    return;
  } else if (head == tail) { // if head and tail pointers are equal
    this->head = nullptr;
    this->tail = nullptr;
  } else if (head == node) {
    TCB* temp = this->head->next;
    this->head = temp;
    temp->prev = nullptr;
  } else if (tail == node) {
    TCB* temp = this->tail->prev;
    this->tail = temp;
    temp->next = nullptr;
  } else {
    TCB* before = node->prev;
    TCB* after = node->next;
    after->prev = before;
    before->next = after;
  }
  return;
}
