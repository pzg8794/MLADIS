import { Task, TaskColumn, TaskDetail, TaskMetric, TaskWorkspace } from '../domain/tasks';
import { createWorkspaceMetadata } from '../domain/workspaceMetadata';
import type { OpsWorkspaceRepository } from './OpsWorkspaceRepository';

function defaultTaskDetail(task: Task): TaskDetail {
  return new TaskDetail(
    task.title === 'Send self check-in instructions'
      ? 'Send self check-in instructions and house guide to the guest 24 hours before arrival.'
      : `Complete "${task.title}" and keep the linked records updated.`,
    task.avatar === 'PG' ? 'Piter Garcia' : 'Maria Rodriguez',
    task.dueTone === 'today' ? 'High' : 'Medium',
    task.due,
    [
      { label: 'Reservation', value: task.meta.find((line) => line.startsWith('Reservation:'))?.replace('Reservation: ', '') || 'R-1042' },
      { label: 'Listing', value: task.meta.find((line) => line.includes('Apt')) || '3 Beds Apt, G-101' },
      { label: 'Guest', value: task.meta.find((line) => line.startsWith('Guest:'))?.replace('Guest: ', '') || 'John Smith' },
    ],
    [
      { label: 'Check-in', value: 'Jun 13, 2026 (3:00 PM)' },
      { label: 'Channel', value: 'Direct Website' },
      { label: 'Nights', value: '3' },
    ],
    'Guest requested early check-in if possible. Include parking and Wi-Fi info.',
    `${task.avatar === 'PG' ? 'Piter Garcia' : 'Maria Rodriguez'} created this task`,
  );
}

function fallbackTaskWorkspace(source: 'fallback' | 'mixed' = 'fallback'): TaskWorkspace {
  const columns = [
    new TaskColumn('In Progress', '6', 'progress', [
      new Task('self-checkin', 'Send self check-in instructions', ['Reservation: R-1042', '3 Beds Apt, Vacation Home & Pool, G-101'], 'Today', 'today', 'MR', 'green', 'progress'),
      new Task('cleaning', 'Confirm cleaning completion', ['Reservation: R-1035', '2 Beds Apt, Vacation Home & Pool'], 'Today', 'today', 'AS', 'lime', 'progress'),
      new Task('deposit-review', 'Review expiring deposit hold', ['Deposit: D-1009', 'Guest: Maria Rodriguez'], 'Today', 'today', 'PG', 'blue', 'progress'),
      new Task('maintenance-bill', 'Generate maintenance bill', ['Work Order: WO-2026-0104', 'AC not cooling - G-101'], 'Today', 'today', 'CM', 'purple', 'progress'),
      new Task('work-order', 'Approve pending work order', ['Work Order: WO-2026-0107', 'Replace ceiling light - Meeting Room 1'], 'Tomorrow', 'soon', 'PG', 'blue', 'progress'),
      new Task('listing-photos', 'Update listing photos', ['Listing: L-1003', '3 Beds Apt, Vacation Home & Pool, G-101'], 'Tomorrow', 'soon', 'DM', 'slate', 'progress'),
    ]),
    new TaskColumn('Waiting', '5', 'waiting', [
      new Task('late-checkin', 'Guest reply: late check-in request', ['Reservation: R-1046', '2 Beds Apt, Vacation Home & Pool'], 'Due Jun 13', 'soon', 'JS', 'photo', 'waiting'),
      new Task('payout', 'Payout confirmation', ['Payment: P-1021', 'Guest: John Smith'], 'Due Jun 13', 'soon', 'PG', 'blue', 'waiting'),
      new Task('vendor-quote', 'Vendor quote approval', ['Work Order: WO-2026-0108', 'TV not turning on - G-101'], 'Due Jun 14', 'soon', 'TS', 'green', 'waiting'),
      new Task('proof-payment', 'Awaiting proof of payment', ['Deposit: D-1011', 'Guest: Ana Lopez'], 'Due Jun 14', 'soon', 'PG', 'blue', 'waiting'),
      new Task('content-review', 'Content review', ['Listing: L-1005', 'Meeting Room 1'], 'Due Jun 15', 'soon', 'DM', 'slate', 'waiting'),
    ]),
    new TaskColumn('Done', '17', 'done', [
      new Task('booking-confirmation', 'Send booking confirmation', ['Reservation: R-1040'], 'Completed Jun 10, 9:15 AM', 'done', 'PG', 'green', 'done'),
      new Task('collect-deposit', 'Collect security deposit', ['Deposit: D-1007'], 'Completed Jun 10, 10:02 AM', 'done', 'PG', 'green', 'done'),
      new Task('inspect-ac', 'Inspect AC repair', ['Work Order: WO-2026-0102'], 'Completed Jun 9, 4:45 PM', 'done', 'CM', 'slate', 'done'),
      new Task('block-dates', 'Block dates for maintenance', ['Property: Conference Room A'], 'Completed Jun 9, 11:12 AM', 'done', 'TS', 'green', 'done'),
      new Task('welcome-message', 'Welcome message sent', ['Reservation: R-1038'], 'Completed Jun 9, 9:08 AM', 'done', 'AS', 'green', 'done'),
    ]),
  ];
  const allTasks = columns.flatMap((column) => column.tasks);
  const detailsByTaskId = Object.fromEntries(allTasks.map((task) => [task.id, defaultTaskDetail(task)]));
  detailsByTaskId.default = defaultTaskDetail(allTasks[0]);

  return new TaskWorkspace(
    [
      new TaskMetric('Overdue', '8', '+3 vs yesterday', 'danger', 'overdue'),
      new TaskMetric('Due Today', '12', '+2 vs yesterday', 'warning', 'today'),
      new TaskMetric('Due This Week', '24', '+6 vs yesterday', 'primary', 'week'),
      new TaskMetric('Completed (7d)', '36', '+12 vs last 7 days', 'success', 'completed'),
      new TaskMetric('Total', '68', 'Active tasks', 'violet', 'total'),
    ],
    columns,
    detailsByTaskId,
    createWorkspaceMetadata(source, source === 'fallback' ? ['workboard API endpoint'] : ['detail projections']),
  );
}

export class TasksRepository {
  constructor(private readonly opsRepository: OpsWorkspaceRepository) {}

  fallback(): TaskWorkspace {
    return fallbackTaskWorkspace();
  }

  async getWorkspace(): Promise<TaskWorkspace> {
    try {
      const snapshot = await this.opsRepository.getWorkboard();
      const fallback = fallbackTaskWorkspace('mixed');
      const metrics = fallback.metrics.map((metric, index) => {
        const apiMetric = snapshot.summaryCards[index];
        if (!apiMetric) return metric;
        return new TaskMetric(apiMetric.label, apiMetric.value, apiMetric.caption, metric.tone, metric.iconKey);
      });
      return new TaskWorkspace(metrics, fallback.columns, fallback.detailsByTaskId, createWorkspaceMetadata('mixed', ['workboard UI projections']));
    } catch {
      return fallbackTaskWorkspace();
    }
  }
}
