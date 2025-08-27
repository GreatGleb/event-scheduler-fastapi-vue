<script setup>
  import { ref, onMounted, onUnmounted } from 'vue';

  const events = ref([]);
  const newEvent = ref({
    title: '',
    description: '',
    event_time: ''
  });

  const pollingCountdown = ref(5);

  let pollingInterval = null;
  let countdownInterval = null;

  const API_URL = 'http://localhost:8000/api';

  const fetchEvents = async () => {
    try {
      const response = await fetch(`${API_URL}/events`);
      if (!response.ok) throw new Error('Network response was not ok');
      events.value = await response.json();
    } catch (error) {
      console.error('Ошибка при загрузке событий:', error);
    }
  };

  const addEvent = async () => {
    if (!newEvent.value.title || !newEvent.value.description || !newEvent.value.event_time) {
      alert('Пожалуйста, заполните все поля');
      return;
    }

    try {
      const response = await fetch(`${API_URL}/events`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newEvent.value)
      });

      if (!response.ok) throw new Error('Failed to add event');

      await fetchEvents();
      pollingCountdown.value = 5;

      newEvent.value.title = '';
      newEvent.value.description = '';
      newEvent.value.event_time = '';

    } catch (error) {
      console.error('Ошибка при добавлении события:', error);
    }
  };

  const completeEvent = async (id) => {
    try {
      await fetch(`${API_URL}/events/${id}`, { method: 'PATCH' });
      await fetchEvents();
      pollingCountdown.value = 5;
    } catch (error) {
      console.error('Ошибка при завершении события:', error);
    }
  };

  onMounted(() => {
    fetchEvents();

    pollingInterval = setInterval(() => {
      fetchEvents();
      pollingCountdown.value = 5;
    }, 5000);

    countdownInterval = setInterval(() => {
      if (pollingCountdown.value > 0) {
        pollingCountdown.value--;
      }
    }, 1000);
  });

  onUnmounted(() => {
    clearInterval(pollingInterval);
    clearInterval(countdownInterval);
  });
</script>

<template>
  <main>
    <h1>Расписание мероприятий</h1>

    <form @submit.prevent="addEvent" class="event-form">
      <input v-model="newEvent.title" placeholder="Название события" required />
      <input v-model="newEvent.description" placeholder="Описание" required />
      <input type="datetime-local" v-model="newEvent.event_time" required />
      <button type="submit">Добавить событие</button>
    </form>

    <div class="toolbar">
      <button @click="fetchEvents" class="refresh-button">Обновить вручную</button>
      <p class="countdown">Следующее автообновление через: {{ pollingCountdown }} сек.</p>
    </div>

    <table>
      <thead>
        <tr>
          <th>Название</th>
          <th>Описание</th>
          <th>Дата и время</th>
          <th>Статус</th>
          <th>Действие</th>
        </tr>
      </thead>
      <tbody>
        <tr v-if="events.length === 0">
          <td colspan="5">Событий пока нет.</td>
        </tr>
        <tr v-for="event in events" :key="event.id">
          <td>{{ event.title }}</td>
          <td>{{ event.description }}</td>
          <td>{{ new Date(event.event_time).toLocaleString() }}</td>
          <td>
            <span :class="['status', event.status]">{{ event.status }}</span>
          </td>
          <td>
            <button @click="completeEvent(event.id)" v-if="event.status === 'pending'">
              Завершить
            </button>
          </td>
        </tr>
      </tbody>
    </table>
  </main>
</template>

<style scoped>
  main {
    max-width: 960px;
    margin: 0 auto;
    padding: 2rem;
    font-family: Inter, system-ui, Avenir, Helvetica, Arial, sans-serif;
  }
  .event-form {
    display: flex;
    gap: 10px;
    margin-bottom: 1rem;
  }
  .event-form input {
    padding: 0.5rem;
    border-radius: 4px;
    border: 1px solid #555;
    flex-grow: 1;
  }
  .event-form button, .refresh-button {
    padding: 0.5rem 1rem;
    border-radius: 4px;
    border: none;
    background-color: #4CAF50;
    color: white;
    cursor: pointer;
  }
  .toolbar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1rem;
  }
  .refresh-button {
    margin: 0;
    background-color: #008CBA;
  }
  .countdown {
    margin: 0;
    font-style: italic;
    color: #aaa;
  }
  table {
    width: 100%;
    border-collapse: collapse;
  }
  th, td {
    border: 1px solid #444;
    padding: 0.75rem;
    text-align: left;
  }
  th {
    background-color: #333;
  }
  .status {
    padding: 0.25rem 0.5rem;
    border-radius: 12px;
    font-weight: bold;
    font-size: 0.8em;
    text-transform: capitalize;
  }
  .status.pending {
    background-color: #ffa500;
    color: #333;
  }
  .status.completed {
    background-color: #4CAF50;
    color: white;
  }
</style>
