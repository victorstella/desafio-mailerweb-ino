import React, { useEffect, useState } from 'react'
import { Heading, Box, Button, Select, Input, Stack, Text, VStack, HStack } from '@chakra-ui/react'
import { apiFetch } from './api'

export default function App() {
  const [token, setToken] = useState(localStorage.getItem('api_token') || '')
  const [rooms, setRooms] = useState([])
  const [selectedRoom, setSelectedRoom] = useState('')
  const [title, setTitle] = useState('New meeting')
  const [startAt, setStartAt] = useState('')
  const [endAt, setEndAt] = useState('')
  const [roomName, setRoomName] = useState('')
  const [roomCapacity, setRoomCapacity] = useState('4')
  const [status, setStatus] = useState('')

  useEffect(() => { fetchRooms() }, [])

  async function fetchRooms() {
    setStatus('Carregando salas...')
    const r = await apiFetch('/rooms/')
    if (!r.ok) { setStatus('Falha ao carregar salas'); return }
    const list = r.data.results || r.data
    setRooms(list || [])
    setStatus('')
    list && list.forEach(loadBookings)
  }

  async function loadBookings(room) {
    const r = await apiFetch(`/rooms/${room.id}/bookings`)
    if (r.ok && Array.isArray(r.data)) {
      setRooms(prev => prev.map(p => p.id === room.id ? { ...p, bookings: r.data } : p))
    }
  }

  function login() {
    const t = window.prompt('Token', token || 'test-token')
    if (!t) return
    setToken(t); localStorage.setItem('api_token', t)
  }
  function logout() { setToken(''); localStorage.removeItem('api_token') }

  async function createBooking(e) {
    e && e.preventDefault()
    setStatus('Preparando agendamento...')
    let roomId = selectedRoom
    if (!roomId) {
      if (!roomName) { setStatus('Forneça o nome da sala'); return }
      const cap = parseInt(roomCapacity, 10) || 1
      setStatus('Criando sala...')
      const rr = await apiFetch('/rooms/', { method: 'POST', token, body: { name: roomName, capacity: cap } })
      if (!rr.ok) { setStatus('Falha ao criar sala'); return }
      const createdRoom = rr.data; roomId = createdRoom.id
      setRooms(prev => [...prev, { ...createdRoom, bookings: [] }])
      setSelectedRoom(roomId)
    }
    setStatus('Criando agendamento...')
    const meetingTitle = (title && title.trim()) ? title : (roomName || '')
    if (!title && meetingTitle) setTitle(meetingTitle)
    const payload = { title: meetingTitle, start_at: startAt, end_at: endAt }
    const r = await apiFetch(`/rooms/${roomId}/bookings`, { method: 'POST', token, body: payload })
    if (!r.ok) { setStatus('Falha ao criar agendamento'); return }
    const created = r.data
    setRooms(prev => prev.map(rm => rm.id === roomId ? { ...rm, bookings: [...(rm.bookings || []), created] } : rm))
    setStatus('Agendamento criado com sucesso!')
  }

  async function cancelBooking(roomId, bookingId) {
    setStatus('Cancelando agendamento...')
    const r = await apiFetch(`/rooms/${roomId}/bookings/${bookingId}/cancel`, { method: 'POST', token })
    if (!r.ok) { setStatus('Falha ao cancelar agendamento'); return }
    const updated = r.data
    setRooms(prev => prev.map(rm => rm.id === roomId ? { ...rm, bookings: (rm.bookings || []).map(b => b.id === bookingId ? updated : b) } : rm))
  }

  async function editBooking(roomId, booking) {
    const newStart = window.prompt('New start_at (ISO)', booking.start_at)
    if (!newStart) return
    const newEnd = window.prompt('New end_at (ISO)', booking.end_at)
    if (!newEnd) return
    setStatus('Atualizando agendamento...')
    const r = await apiFetch(`/rooms/${roomId}/bookings/${booking.id}`, { method: 'PUT', token, body: { start_at: newStart, end_at: newEnd } })
    if (!r.ok) { setStatus('Falha ao atualizar agendamento'); return }
    setRooms(prev => prev.map(rm => rm.id === roomId ? { ...rm, bookings: (rm.bookings || []).map(b => b.id === booking.id ? r.data : b) } : rm))
  }

  return (
    <VStack align="stretch" spacing={6}>
      <HStack justify="space-between">
        <Heading size="md">Meeting Room — UI</Heading>
        <HStack>
          <Button onClick={login}>Login</Button>
          <Button onClick={logout}>Logout</Button>
          <Text fontSize="sm">Token: {token ? 'logado' : 'deslogado'}</Text>
        </HStack>
      </HStack>

      <Box>
        <Button onClick={fetchRooms} size="sm">Atualizar Salas</Button>
      </Box>

      <HStack align="start" spacing={8}>
        <Box flex={1}>
          <Heading size="sm">Salas</Heading>
          <VStack align="stretch" spacing={4} mt={3}>
            {rooms.map(r => (
              <Box key={r.id} borderWidth={1} p={3}>
                <HStack justify="space-between">
                  <Text fontWeight="bold">{r.name}</Text>
                  <Text fontSize="sm">Capacidade: {r.capacity}</Text>
                </HStack>
                <Text fontSize="sm">Reuniões Agendadas na Sala: {(r.bookings || []).length}</Text>
                <VStack align="stretch" mt={2}>
                  {(r.bookings || []).map(b => (
                    <Box key={b.id} p={2} borderWidth={1} bg="gray.50">
                      <HStack justify="space-between">
                        <Text fontWeight="semibold">{b.title}</Text>
                        <Text fontSize="sm">{b.start_at} → {b.end_at}</Text>
                      </HStack>
                      <HStack mt={2}>
                        <Button size="sm" onClick={() => cancelBooking(r.id, b.id)}>Cancelar</Button>
                        <Button size="sm" onClick={() => editBooking(r.id, b)}>Editar</Button>
                        <Text fontSize="sm">Status: {b.status}</Text>
                      </HStack>
                    </Box>
                  ))}
                </VStack>
              </Box>
            ))}
          </VStack>
        </Box>

        <Box width="360px">
          <Heading size="sm">Agendar</Heading>
          <Stack spacing={3} mt={3}>
            <Select value={selectedRoom} onChange={e => setSelectedRoom(e.target.value)}>
              <option value="">--selecionar-- (ou criar abaixo)</option>
              {rooms.map(r => <option key={r.id} value={r.id}>{r.name}</option>)}
            </Select>
            {!selectedRoom && (
              <>
                <Input placeholder="Nome da sala" value={roomName} onChange={e => setRoomName(e.target.value)} />
                <Input placeholder="Capacidade da sala" value={roomCapacity} onChange={e => setRoomCapacity(e.target.value)} />
              </>
            )}
            <Input placeholder="Título da reunião" value={title} onChange={e => setTitle(e.target.value)} />
            <Input placeholder="YYYY-MM-DDThh:mm:ssZ" value={startAt} onChange={e => setStartAt(e.target.value)} />
            <Input placeholder="YYYY-MM-DDThh:mm:ssZ" value={endAt} onChange={e => setEndAt(e.target.value)} />
            <Button onClick={createBooking}>Criar Agendamento</Button>
            <Text>Log: {status}</Text>
          </Stack>
        </Box>
      </HStack>
    </VStack>
  )
}
