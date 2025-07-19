from django.test import TestCase, Client
from django.utils import timezone
from datetime import datetime
from todo.models import Task


# Create your tests here.
class SampleTestCase(TestCase):
    def test_sample1(self):
        self.assertEqual(1 + 2, 3)


class TaskModelTestCase(TestCase):
    def test_create_task1(self):
        due = timezone.make_aware(datetime(2024, 6, 30, 23, 59, 59))
        task = Task(title='task1', due_at=due)
        task.save()

        task = Task.objects.get(pk=task.pk)
        self.assertEqual(task.title, 'task1')
        self.assertFalse(task.completed)
        self.assertEqual(task.due_at, due)

    def test_create_task2(self):
        task = Task(title='task2')
        task.save()

        task = Task.objects.get(pk=task.pk)
        self.assertEqual(task.title, 'task2')
        self.assertFalse(task.completed)
        self.assertEqual(task.due_at, None)

    def test_is_overdue_future(self):
        due = timezone.make_aware(datetime(2024, 6, 30, 23, 59, 59))
        current = timezone.make_aware(datetime(2024, 6, 30, 0, 0, 0))
        task = Task(title='task1', due_at=due)
        task.save()

        self.assertFalse(task.is_overdue(current))

    def test_is_overdue_past(self):
        due = timezone.make_aware(datetime(2024, 6, 30, 23, 59, 59))
        current = timezone.make_aware(datetime(2024, 7, 1, 0, 0, 0))
        task = Task(title='task1', due_at=due)
        task.save()

        self.assertTrue(task.is_overdue(current))

    def test_is_overdue_node(self):
        due = None
        current = timezone.make_aware(datetime(2024, 7, 1, 0, 0, 0))
        task = Task(title='task1', due_at=due)
        task.save()

        self.assertFalse(task.is_overdue(current))


class TodoViewTestCase(TestCase):
    def test_index_get(self):
        client = Client()
        response = client.get('/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.templates[0].name, 'todo/index.html')
        self.assertEqual(len(response.context['tasks']), 0)

    def test_index_post(self):
        client = Client()
        data = {'title': 'Test Task', 'due_at': '2024-06-30 23:59:59'}
        response = client.post('/', data)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.templates[0].name, 'todo/index.html')
        self.assertEqual(len(response.context['tasks']), 1)

    def test_index_get_order_post(self):
        task1 = Task(title='task1', due_at=timezone.make_aware(datetime(2024, 7, 1)))
        task1.save()
        task2 = Task(title='task2', due_at=timezone.make_aware(datetime(2024, 8, 1)))
        task2.save()
        client = Client()
        response = client.get('/?order=post')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.templates[0].name, 'todo/index.html')
        self.assertEqual(response.context['tasks'][0], task2)
        self.assertEqual(response.context['tasks'][1], task1)

    def test_index_get_order_due(self):
        task1 = Task(title='task1', due_at=timezone.make_aware(datetime(2024, 7, 1)))
        task1.save()
        task2 = Task(title='task2', due_at=timezone.make_aware(datetime(2024, 8, 1)))
        task2.save()
        client = Client()
        response = client.get('/?order=due')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.templates[0].name, 'todo/index.html')
        self.assertEqual(response.context['tasks'][0], task1)
        self.assertEqual(response.context['tasks'][1], task2)

    def test_detail_get_success(self):
        task = Task(title='task1', due_at=timezone.make_aware(datetime(2024, 7, 1)))
        task.save()
        client = Client()
        response = client.get('/{}/'.format(task.pk))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.templates[0].name, 'todo/detail.html')
        self.assertEqual(response.context['task'], task)

    def test_detail_get_fail(self):
        client = Client()
        response = client.get('/1/')

        self.assertEqual(response.status_code, 404)

    def test_delete_success(self):
        task = Task(title='task1', due_at=timezone.make_aware(datetime(2024, 7, 1)))
        task.save()
        task_id = task.pk
        client = Client()
        
        # detailにアクセス.
        response = client.post('/{}/delete/'.format(task.pk))
        self.assertEqual(response.status_code, 302)
        
        # task1は削除ずみ.
        task = Task.objects.filter(pk=task.pk)
        self.assertEqual(len(task), 0)
        
        # 削除済みのtaskにアクセス.
        response = client.get('/{}/'.format(task_id))
        self.assertEqual(response.status_code, 404)

    # 検索機能のテスト
    def test_search_function(self):
        Task.objects.create(title='Apple Banana')
        Task.objects.create(title='Banana Cherry')
        Task.objects.create(title='Apple Orange')

        client = Client()
        response = client.get('/?q=Banana')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['tasks']), 2)

        response = client.get('/?q=Orange')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['tasks']), 1)
        self.assertEqual(response.context['tasks'][0].title, 'Apple Orange')

        response = client.get('/?q=Grape')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['tasks']), 0)

    # タスクの完了・未完了切り替え機能のテスト
    def test_complete_view(self):
        task = Task.objects.create(title='Incomplete Task')
        self.assertFalse(task.completed)
        client = Client()
        response = client.get('/{}/complete/'.format(task.pk))
        self.assertRedirects(response, '/')
        task.refresh_from_db()
        self.assertTrue(task.completed, 'Task should be marked as completed')
        response = client.get('/{}/complete/'.format(task.pk))
        task.refresh_from_db()
        self.assertFalse(task.completed, 'Task should be marked as not completed')

    # 完了・未完了での絞り込み機能のテスト
    def test_filter_function(self):
        Task.objects.create(title='Task 1', completed=True)
        Task.objects.create(title='Task 2', completed=False)
        Task.objects.create(title='Task 3', completed=True)

        client = Client()
        response = client.get('/?filter=complete')
        self.assertEqual(len(response.context['tasks']), 2)
        self.assertTrue(all(task.completed for task in response.context['tasks']))

        response = client.get('/?filter=incomplete')
        self.assertEqual(len(response.context['tasks']), 1)
        self.assertEqual(response.context['tasks'][0].title, 'Task 2')
        self.assertFalse(any(task.completed for task in response.context['tasks']))
        response = client.get('/')
        self.assertEqual(len(response.context['tasks']), 3)
    
    # コメント機能のテスト
    def test_comment_creation_and_display(self):
        client = Client()
        comment_text = "This is a test comment."
        data = {
            'title': 'Task with comment',
            'due_at': '',
            'comment': comment_text,
        }
        response = client.post('/', data, follow=True)
        self.assertEqual(response.status_code, 200)
        created_task = Task.objects.get(title='Task with comment')
        self.assertEqual(created_task.comment, comment_text)
        response = client.get('/{}/'.format(created_task.pk))
        self.assertContains(response, comment_text)
        long_comment = "This is a very long comment to test the truncatechars filter in the index page."
        Task.objects.create(title='Long comment task', comment=long_comment)
        response = client.get('/')
        self.assertContains(response, '…') 
        self.assertNotContains(response, long_comment)

    # 絞り込みとソートの組み合わせ機能のテスト
    def test_filter_and_sort_combination(self):
        now = timezone.now()
        Task.objects.create(title='Incomplete, due later', completed=False, due_at=now + timezone.timedelta(days=2))
        Task.objects.create(title='Completed, due earlier', completed=True, due_at=now + timezone.timedelta(days=1))
        Task.objects.create(title='Incomplete, due earlier', completed=False, due_at=now + timezone.timedelta(days=1))
        client = Client()
        response = client.get('/?filter=incomplete&order=due')
        self.assertEqual(response.status_code, 200)
        tasks = response.context['tasks']
        self.assertEqual(len(tasks), 2)
        self.assertEqual(tasks[0].title, 'Incomplete, due earlier')
        self.assertEqual(tasks[1].title, 'Incomplete, due later')
