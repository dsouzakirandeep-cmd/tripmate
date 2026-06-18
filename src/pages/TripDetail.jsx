import { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { supabase } from '../supabaseClient';

export default function TripDetail({ session }) {
  const { id } = useParams();
  const navigate = useNavigate();
  const user = session.user;
  const [trip, setTrip] = useState(null);
  const [activeTab, setActiveTab] = useState('plan');
  const [events, setEvents] = useState([]);
  const [expenses, setExpenses] = useState([]);
  const [messages, setMessages] = useState([]);
  const [members, setMembers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [newMsg, setNewMsg] = useState('');
  const [aiLoading, setAiLoading] = useState(false);
  const [showAiModal, setShowAiModal] = useState(false);
  const [aiPrefs, setAiPrefs] = useState({
    ageGroups: [],
    travelStyle: '',
    interests: [],
    budget: '',
    transport: '',
    restrictions: ''
  });
  const chatRef = useRef(null);

  const [showEventModal, setShowEventModal] = useState(false);
  const [showExpenseModal, setShowExpenseModal] = useState(false);
  const [showMemberModal, setShowMemberModal] = useState(false);
  const [newEvent, setNewEvent] = useState({ title:'', event_date:'', event_time:'', location:'', notes:'' });
  const [newExpense, setNewExpense] = useState({ title:'', amount:'', paid_by:'', category:'💰' });
  const [newMemberName, setNewMemberName] = useState('');

  useEffect(() => {
    fetchAll();
    const msgSub = supabase.channel('messages:'+id)
      .on('postgres_changes', { event:'INSERT', schema:'public', table:'messages', filter:`trip_id=eq.${id}` },
        payload => setMessages(prev => [...prev, payload.new]))
      .subscribe();
    return () => supabase.removeChannel(msgSub);
  }, [id]);

  useEffect(() => {
    if (chatRef.current) chatRef.current.scrollTop = chatRef.current.scrollHeight;
  }, [messages]);

  async function fetchAll() {
    setLoading(true);
    const [tripRes, eventsRes, expensesRes, messagesRes, membersRes] = await Promise.all([
      supabase.from('trips').select('*').eq('id', id).single(),
      supabase.from('events').select('*').eq('trip_id', id).order('event_date').order('event_time'),
      supabase.from('expenses').select('*').eq('trip_id', id).order('created_at'),
      supabase.from('messages').select('*, profile:profiles(name)').eq('trip_id', id).order('created_at'),
      supabase.from('trip_members').select('*, profile:profiles(name, id)').eq('trip_id', id),
    ]);
    if (tripRes.data) setTrip(tripRes.data);
    if (eventsRes.data) setEvents(eventsRes.data);
    if (expensesRes.data) setExpenses(expensesRes.data);
    if (messagesRes.data) setMessages(messagesRes.data);
    if (membersRes.data) setMembers(membersRes.data);
    setLoading(false);
  }

  function toggleMulti(field, value) {
    setAiPrefs(prev => ({
      ...prev,
      [field]: prev[field].includes(value)
        ? prev[field].filter(v => v !== value)
        : [...prev[field], value]
    }));
  }

  async function generateItinerary() {
    if (!trip) return;
    if (!aiPrefs.travelStyle || !aiPrefs.budget || !aiPrefs.transport) {
      alert('Please fill in Travel Style, Budget, and Transportation before generating.');
      return;
    }
    setShowAiModal(false);
    setAiLoading(true);
    try {
      const prompt = `List 6 activities for a trip to ${trip.destination}.
Group: ${aiPrefs.ageGroups.join(', ') || 'adults'}
Style: ${aiPrefs.travelStyle}
Budget: ${aiPrefs.budget}
Transport: ${aiPrefs.transport}

IMPORTANT: Return ONLY this exact JSON format, nothing else:
[{"title":"Activity Name","event_date":"${trip.start_date}","event_time":"09:00","location":"Place Name","notes":"Cost $X | Xhrs"}]

Keep each notes field under 50 characters. Return exactly 6 items. No explanation.`;

      const response = await fetch('/.netlify/functions/generate-itinerary', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          destination: trip.destination,
          start_date: trip.start_date,
          end_date: trip.end_date,
          prefs: {
            ageGroups: aiPrefs.ageGroups.join(', '),
            travelStyle: aiPrefs.travelStyle,
            budget: aiPrefs.budget,
            transport: aiPrefs.transport,
            restrictions: aiPrefs.restrictions
          }
        })
      });

      const text = await response.text();
      
      // Smart repair - finds only complete JSON objects
      function repairJSON(raw) {
        const start = raw.indexOf('[');
        if (start === -1) throw new Error('No JSON found');
        let jsonStr = raw.slice(start);
        let lastCompleteEnd = -1;
        let depth = 0;
        let inString = false;
        let escaped = false;
        for (let i = 0; i < jsonStr.length; i++) {
          const ch = jsonStr[i];
          if (escaped) { escaped = false; continue; }
          if (ch === '\\' && inString) { escaped = true; continue; }
          if (ch === '"') { inString = !inString; continue; }
          if (inString) continue;
          if (ch === '{') depth++;
          if (ch === '}') { depth--; if (depth === 0) lastCompleteEnd = i; }
        }
        if (lastCompleteEnd === -1) throw new Error('No complete objects found');
        const trimmed = jsonStr.slice(0, lastCompleteEnd + 1) + ']';
        return JSON.parse(trimmed.replace(/,\s*\]/g, ']'));
      const data = await response.json();
      const aiText = data.content[0].text;
      const start = aiText.indexOf('[');
      const end = aiText.lastIndexOf(']');
      if (start === -1 || end === -1) throw new Error('Invalid response from AI');
      const jsonStr = aiText.slice(start, end + 1);
      const cleaned = jsonStr
        .replace(/[\u0000-\u001F\u007F-\u009F]/g, ' ')
        .replace(/,\s*]/g, ']')
        .replace(/,\s*}/g, '}');
      const suggestions = JSON.parse(cleaned);
      const COLORS = ['#378ADD','#1D9E75','#EF9F27','#D85A30','#7F77DD','#D4537E'];
      for (let i = 0; i < suggestions.length; i++) {
        const s = suggestions[i];
      for (let i = 0; i < suggestions.length; i++) {
        const s = suggestions[i];
        await supabase.from('events').insert([{
          trip_id: id,
          title: s.title || 'Activity',
          event_date: s.event_date,
          event_time: s.event_time || '09:00',
          location: s.location || '',
          notes: (s.notes || '').slice(0, 200),
          color: COLORS[i % COLORS.length],
          added_by: user.id
        }]);
      }
      fetchAll();
      alert('✅ AI itinerary generated! Check your Plan tab.');
    } catch (err) {
      alert('Error: ' + err.message);
    }
    setAiLoading(false);
  }

  async function addEvent() {
    if (!newEvent.title || !newEvent.event_date) return alert('Please enter title and date.');
    const COLORS = ['#378ADD','#1D9E75','#EF9F27','#D85A30','#7F77DD','#D4537E'];
    const color = COLORS[events.length % COLORS.length];
    const { error } = await supabase.from('events').insert([{ ...newEvent, trip_id: id, added_by: user.id, color }]);
    if (error) return alert(error.message);
    setShowEventModal(false);
    setNewEvent({ title:'', event_date:'', event_time:'', location:'', notes:'' });
    fetchAll();
  }

  async function addExpense() {
    if (!newExpense.title || !newExpense.amount) return alert('Please enter title and amount.');
    const { error } = await supabase.from('expenses').insert([{
      title: newExpense.title,
      amount: parseFloat(newExpense.amount),
      paid_by: newExpense.paid_by || user.id,
      category: newExpense.category,
      trip_id: id,
      expense_date: new Date().toISOString().split('T')[0]
    }]);
    if (error) return alert(error.message);
    setShowExpenseModal(false);
    setNewExpense({ title:'', amount:'', paid_by:'', category:'💰' });
    fetchAll();
  }

  async function sendMessage() {
    if (!newMsg.trim()) return;
    await supabase.from('messages').insert([{ trip_id: id, user_id: user.id, text: newMsg.trim() }]);
    setNewMsg('');
  }

  async function updateMemberStatus(memberId, status) {
    await supabase.from('trip_members').update({ status }).eq('id', memberId);
    fetchAll();
  }

  async function removeMember(memberId) {
    if (!window.confirm('Remove this member from the trip?')) return;
    await supabase.from('trip_members').delete().eq('id', memberId);
    fetchAll();
  }

  const acceptedMembers = members.filter(m => m.status === 'accepted');
  const totalExp = expenses.reduce((s, e) => s + parseFloat(e.amount), 0);
  const perPerson = acceptedMembers.length ? Math.round(totalExp / acceptedMembers.length) : 0;
  const fmt = n => '$' + Number(n).toLocaleString('en-US');

  const eventsByDate = events.reduce((acc, e) => {
    const d = e.event_date || 'TBD';
    if (!acc[d]) acc[d] = [];
    acc[d].push(e);
    return acc;
  }, {});

  const CATS = ['💰','🏨','🚕','🍽️','⛵','🏄','🎟️','🛍️'];

  function ChipGroup({ label, options, field, multi }) {
    return (
      <div style={{marginBottom:'14px'}}>
        <div style={styles.label}>{label}</div>
        <div style={{display:'flex', flexWrap:'wrap', gap:'8px', marginTop:'6px'}}>
          {options.map(opt => {
            const selected = multi
              ? aiPrefs[field].includes(opt.value)
              : aiPrefs[field] === opt.value;
            return (
              <button key={opt.value}
                onClick={() => multi ? toggleMulti(field, opt.value) : setAiPrefs(p => ({...p, [field]: opt.value}))}
                style={{
                  padding:'8px 14px', borderRadius:'20px', border:'1.5px solid',
                  borderColor: selected ? '#378ADD' : '#e2e8f0',
                  background: selected ? '#EBF4FF' : '#fff',
                  color: selected ? '#185FA5' : '#555',
                  fontSize:'13px', fontWeight: selected ? '600' : '400',
                  cursor:'pointer'
                }}>
                {opt.label}
              </button>
            );
          })}
        </div>
      </div>
    );
  }

  if (loading) return <div style={{display:'flex',alignItems:'center',justifyContent:'center',height:'100vh',fontSize:'32px'}}>✈️</div>;
  if (!trip) return <div style={{padding:'24px',textAlign:'center'}}>Trip not found</div>;

  return (
    <div style={styles.container}>
      <div style={styles.topBar}>
        <button style={styles.backBtn} onClick={() => navigate('/dashboard')}>←</button>
        <div style={styles.topTitle}>{trip.name} {trip.emoji}</div>
        <button style={styles.inviteBtn} onClick={() => { navigator.clipboard?.writeText(window.location.href); alert('Link copied!'); }}>🔗</button>
      </div>

      <div style={styles.tabBar}>
        {['plan','expenses','chat','members'].map(tab => (
          <button key={tab} style={{...styles.tabBtn, ...(activeTab===tab ? styles.tabActive : {})}}
            onClick={() => setActiveTab(tab)}>
            <span style={{fontSize:'18px'}}>{tab==='plan'?'📅':tab==='expenses'?'💳':tab==='chat'?'💬':'👥'}</span>
            <span>{tab.charAt(0).toUpperCase()+tab.slice(1)}</span>
          </button>
        ))}
      </div>

      {activeTab === 'plan' && (
        <div style={styles.content}>
          {Object.keys(eventsByDate).sort().map(date => (
            <div key={date} style={{marginBottom:'16px'}}>
              <div style={styles.dayLabel}>
                {date !== 'TBD' ? new Date(date+'T12:00:00').toLocaleDateString('en-US',{weekday:'short',month:'short',day:'numeric'}) : 'TBD'}
              </div>
              {eventsByDate[date].map(ev => (
                <div key={ev.id} style={styles.eventCard}>
                  <div style={styles.eventTime}>{ev.event_time?.slice(0,5) || '--'}</div>
                  <div style={{...styles.eventDot, background: ev.color || '#378ADD'}} />
                  <div style={{flex:1}}>
                    <div style={styles.eventTitle}>{ev.title}</div>
                    {ev.location && <div style={styles.eventSub}>📍 {ev.location}</div>}
                    {ev.notes && <div style={styles.eventNotes}>{ev.notes}</div>}
                  </div>
                </div>
              ))}
            </div>
          ))}
          {events.length === 0 && <div style={styles.emptyState}>No events yet — add one or generate with AI!</div>}
          <button style={styles.addBtn} onClick={() => setShowEventModal(true)}>＋ Add event manually</button>
          <div style={styles.aiCard}>
            <div style={styles.aiLabel}>🤖 AI Smart Itinerary Generator</div>
            <div style={styles.aiText}>
              Tell me about your group and I'll create a personalized itinerary for <strong>{trip?.destination}</strong> — with travel times, ticket prices, and age-appropriate activities!
            </div>
            <button onClick={() => setShowAiModal(true)} disabled={aiLoading}
              style={{marginTop:'10px',width:'100%',padding:'11px',background:aiLoading?'#aaa':'linear-gradient(135deg,#378ADD,#185FA5)',color:'#fff',border:'none',borderRadius:'10px',fontSize:'14px',fontWeight:'600',cursor:aiLoading?'not-allowed':'pointer'}}>
              {aiLoading ? '🤖 Generating your itinerary...' : '✨ Customize & Generate Itinerary'}
            </button>
          </div>
        </div>
      )}

      {activeTab === 'expenses' && (
        <div style={styles.content}>
          <div style={styles.expSummary}>
            <div style={styles.expTotal}>{fmt(totalExp)}</div>
            <div style={styles.expSub}>Total expenses</div>
            <div style={styles.expPer}>{fmt(perPerson)} per person · {acceptedMembers.length} confirmed</div>
          </div>
          <div style={styles.sectionTitle}>All expenses</div>
          {expenses.map(exp => {
            const payer = members.find(m => m.profile?.id === exp.paid_by);
            return (
              <div key={exp.id} style={styles.expItem}>
                <div style={{flex:1}}>
                  <div style={styles.expName}>{exp.category} {exp.title}</div>
                  <div style={styles.expWho}>Paid by {payer?.profile?.name || 'Unknown'}</div>
                </div>
                <div style={styles.expAmt}>{fmt(exp.amount)}</div>
              </div>
            );
          })}
          {expenses.length === 0 && <div style={styles.emptyState}>No expenses yet!</div>}
          <button style={styles.addBtn} onClick={() => { setNewExpense({...newExpense, paid_by: user.id}); setShowExpenseModal(true); }}>＋ Add expense</button>
        </div>
      )}

      {activeTab === 'chat' && (
        <div style={{...styles.chatWrap}}>
          <div style={styles.chatMessages} ref={chatRef}>
            {messages.map(msg => {
              const isMe = msg.user_id === user.id;
              return (
                <div key={msg.id} style={{...styles.msgWrap, alignItems: isMe ? 'flex-end' : 'flex-start'}}>
                  {!isMe && <div style={styles.msgSender}>{msg.profile?.name || 'Member'}</div>}
                  <div style={{...styles.bubble, ...(isMe ? styles.bubbleOut : styles.bubbleIn)}}>{msg.text}</div>
                  <div style={styles.msgTime}>{new Date(msg.created_at).toLocaleTimeString('en-US',{hour:'numeric',minute:'2-digit'})}</div>
                </div>
              );
            })}
            {messages.length === 0 && <div style={styles.emptyState}>No messages yet — say hello! 👋</div>}
          </div>
          <div style={styles.chatInput}>
            <input style={styles.chatInputField} placeholder="Message the group..."
              value={newMsg} onChange={e => setNewMsg(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && sendMessage()} />
            <button style={styles.sendBtn} onClick={sendMessage}>
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="2"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22,2 15,22 11,13 2,9"/></svg>
            </button>
          </div>
        </div>
      )}

      {activeTab === 'members' && (
        <div style={styles.content}>
          <div style={styles.memberStats}>
            {[['Going', members.filter(m=>m.status==='accepted').length, '#F0FDF4', '#166534'],
              ['Pending', members.filter(m=>m.status==='pending').length, '#FEF9EE', '#854F0B'],
              ['Declined', members.filter(m=>m.status==='declined').length, '#FEF2F2', '#991B1B']
            ].map(([label, count, bg, color]) => (
              <div key={label} style={{...styles.statBox, background: bg}}>
                <div style={{fontSize:'22px', fontWeight:'700', color}}>{count}</div>
                <div style={{fontSize:'11px', color, marginTop:'2px'}}>{label}</div>
              </div>
            ))}
          </div>
          {['accepted','pending','declined'].map(status => {
            const group = members.filter(m => m.status === status);
            if (!group.length) return null;
            const labels = {accepted:'✓ Going', pending:'⏳ Awaiting response', declined:'✕ Declined'};
            return (
              <div key={status}>
                <div style={styles.sectionTitle}>{labels[status]} ({group.length})</div>
                {group.map(m => {
                  const isYou = m.profile?.id === user.id;
                  return (
                    <div key={m.id} style={{...styles.memberCard, opacity: status==='declined' ? 0.6 : 1}}>
                      <div style={{...styles.memberAvatar, background: status==='declined'?'#ccc':'#378ADD'}}>
                        {m.profile?.name?.slice(0,2).toUpperCase() || '??'}
                      </div>
                      <div style={{flex:1}}>
                        <div style={styles.memberName}>{m.profile?.name || 'Unknown'} {isYou && <span style={styles.youBadge}>You</span>}</div>
                        <div style={styles.memberRole}>{m.role === 'organizer' ? 'Trip organizer' : 'Member'}</div>
                      </div>
                      {!isYou && (
                        <div style={{display:'flex', gap:'6px'}}>
                          {status !== 'accepted' && <button style={{...styles.actionBtn, background:'#F0FDF4', color:'#166534'}} onClick={() => updateMemberStatus(m.id, 'accepted')}>✓</button>}
                          {status !== 'declined' && <button style={{...styles.actionBtn, background:'#FEF2F2', color:'#991B1B'}} onClick={() => updateMemberStatus(m.id, 'declined')}>✕</button>}
                          <button style={{...styles.actionBtn, background:'#f0f4f8', color:'#888'}} onClick={() => removeMember(m.id)}>🗑</button>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            );
          })}
          <button style={styles.addBtn} onClick={() => setShowMemberModal(true)}>＋ Invite member</button>
          <div style={styles.inviteLinkCard}>
            <div style={styles.inviteLinkLabel}>🔗 Share invite link</div>
            <div style={{display:'flex', gap:'8px', alignItems:'center'}}>
              <div style={styles.inviteLinkText}>{window.location.href}</div>
              <button style={styles.copyBtn} onClick={() => { navigator.clipboard?.writeText(window.location.href); alert('Copied!'); }}>Copy</button>
            </div>
          </div>
        </div>
      )}

      {/* AI PREFERENCES MODAL */}
      {showAiModal && (
        <div style={styles.overlay} onClick={e => e.target===e.currentTarget && setShowAiModal(false)}>
          <div style={{...styles.modal, maxHeight:'90vh', overflowY:'auto'}}>
            <div style={styles.handle} />
            <div style={styles.modalTitle}>🤖 Customize Your Itinerary</div>
            <div style={{fontSize:'13px', color:'#888', marginBottom:'16px'}}>
              Tell me about your group and I'll create a personalized plan for <strong>{trip?.destination}</strong>
            </div>
            <ChipGroup label="👥 Who's coming?" field="ageGroups" multi={true} options={[
              {label:'👶 Toddlers', value:'toddlers'},
              {label:'🧒 Kids (4-12)', value:'kids'},
              {label:'🧑 Teens', value:'teens'},
              {label:'🧑‍💼 Adults', value:'adults'},
              {label:'👴 Seniors (60+)', value:'seniors'},
            ]} />
            <ChipGroup label="🎯 Travel style" field="travelStyle" multi={false} options={[
              {label:'😌 Relaxed', value:'relaxed'},
              {label:'⚖️ Balanced', value:'balanced'},
              {label:'🚀 Packed', value:'packed'},
            ]} />
            <ChipGroup label="❤️ Interests" field="interests" multi={true} options={[
              {label:'🏛️ Culture', value:'culture'},
              {label:'🍽️ Food', value:'food'},
              {label:'🌿 Nature', value:'nature'},
              {label:'🛍️ Shopping', value:'shopping'},
              {label:'🎭 Arts', value:'arts'},
              {label:'🏖️ Beach', value:'beach'},
              {label:'🎢 Adventure', value:'adventure'},
              {label:'📸 Photography', value:'photography'},
            ]} />
            <ChipGroup label="💰 Budget" field="budget" multi={false} options={[
              {label:'💵 Budget', value:'budget'},
              {label:'💳 Moderate', value:'moderate'},
              {label:'💎 Luxury', value:'luxury'},
            ]} />
            <ChipGroup label="🚗 Getting around" field="transport" multi={false} options={[
              {label:'🚗 Own car', value:'own car'},
              {label:'🚌 Public transport', value:'public transport'},
              {label:'🚕 Taxi/Uber', value:'taxi'},
              {label:'🚶 Walking', value:'walking'},
              {label:'🔀 Mix', value:'mixed'},
            ]} />
            <div style={{marginBottom:'16px'}}>
              <div style={styles.label}>⚠️ Special requirements?</div>
              <input style={{...styles.input, marginTop:'6px'}}
                placeholder="e.g. wheelchair accessible, vegetarian, avoid crowds..."
                value={aiPrefs.restrictions}
                onChange={e => setAiPrefs(p => ({...p, restrictions: e.target.value}))} />
            </div>
            <div style={styles.btnRow}>
              <button style={styles.cancelBtn} onClick={() => setShowAiModal(false)}>Cancel</button>
              <button style={styles.saveBtn} onClick={generateItinerary}>✨ Generate</button>
            </div>
          </div>
        </div>
      )}

      {showEventModal && (
        <div style={styles.overlay} onClick={e => e.target===e.currentTarget && setShowEventModal(false)}>
          <div style={styles.modal}>
            <div style={styles.handle} />
            <div style={styles.modalTitle}>Add event</div>
            {[['Title','text','title','e.g. Beach day'],['Date','date','event_date',''],['Time','time','event_time',''],['Location','text','location','e.g. Calangute Beach'],['Notes','text','notes','Any details...']].map(([label,type,key,ph]) => (
              <div key={key} style={{marginBottom:'10px'}}>
                <div style={styles.label}>{label}</div>
                <input style={styles.input} type={type} placeholder={ph} value={newEvent[key]}
                  onChange={e => setNewEvent({...newEvent, [key]: e.target.value})} />
              </div>
            ))}
            <div style={styles.btnRow}>
              <button style={styles.cancelBtn} onClick={() => setShowEventModal(false)}>Cancel</button>
              <button style={styles.saveBtn} onClick={addEvent}>Add event</button>
            </div>
          </div>
        </div>
      )}

      {showExpenseModal && (
        <div style={styles.overlay} onClick={e => e.target===e.currentTarget && setShowExpenseModal(false)}>
          <div style={styles.modal}>
            <div style={styles.handle} />
            <div style={styles.modalTitle}>Add expense</div>
            <div style={{marginBottom:'10px'}}>
              <div style={styles.label}>Category</div>
              <div style={{display:'flex', gap:'8px', flexWrap:'wrap', marginBottom:'4px'}}>
                {CATS.map(cat => (
                  <span key={cat} style={{fontSize:'22px', padding:'6px', borderRadius:'10px', cursor:'pointer', background: newExpense.category===cat?'#EBF4FF':'#f0f4f8'}}
                    onClick={() => setNewExpense({...newExpense, category: cat})}>{cat}</span>
                ))}
              </div>
            </div>
            <div style={{marginBottom:'10px'}}>
              <div style={styles.label}>What was it for?</div>
              <input style={styles.input} placeholder="e.g. Hotel deposit" value={newExpense.title}
                onChange={e => setNewExpense({...newExpense, title: e.target.value})} />
            </div>
            <div style={{marginBottom:'10px'}}>
              <div style={styles.label}>Amount ($)</div>
              <input style={styles.input} type="number" placeholder="0" value={newExpense.amount}
                onChange={e => setNewExpense({...newExpense, amount: e.target.value})} />
            </div>
            <div style={{marginBottom:'10px'}}>
              <div style={styles.label}>Paid by</div>
              <select style={styles.input} value={newExpense.paid_by} onChange={e => setNewExpense({...newExpense, paid_by: e.target.value})}>
                {acceptedMembers.map(m => <option key={m.profile?.id} value={m.profile?.id}>{m.profile?.name}</option>)}
              </select>
            </div>
            <div style={styles.btnRow}>
              <button style={styles.cancelBtn} onClick={() => setShowExpenseModal(false)}>Cancel</button>
              <button style={styles.saveBtn} onClick={addExpense}>Add expense</button>
            </div>
          </div>
        </div>
      )}

      {showMemberModal && (
        <div style={styles.overlay} onClick={e => e.target===e.currentTarget && setShowMemberModal(false)}>
          <div style={styles.modal}>
            <div style={styles.handle} />
            <div style={styles.modalTitle}>Invite member</div>
            <div style={{marginBottom:'10px'}}>
              <div style={styles.label}>Their name</div>
              <input style={styles.input} placeholder="e.g. Priya Sharma" value={newMemberName}
                onChange={e => setNewMemberName(e.target.value)} />
            </div>
            <div style={{background:'#FEF9EE', borderRadius:'12px', padding:'12px', fontSize:'13px', color:'#854F0B', marginBottom:'12px'}}>
              💡 Share the invite link with them so they can join and set their own status.
            </div>
            <div style={styles.btnRow}>
              <button style={styles.cancelBtn} onClick={() => setShowMemberModal(false)}>Cancel</button>
              <button style={styles.saveBtn} onClick={() => { alert('Share this link: ' + window.location.href); setShowMemberModal(false); }}>Copy invite link</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

const styles = {
  container: { maxWidth:'430px', margin:'0 auto', minHeight:'100vh', background:'#f8fafc', display:'flex', flexDirection:'column' },
  topBar: { background:'#fff', padding:'12px 16px', borderBottom:'1px solid #f0f0f0', display:'flex', alignItems:'center', gap:'12px', flexShrink:0 },
  backBtn: { width:'36px', height:'36px', borderRadius:'50%', background:'#f5f7fa', border:'none', fontSize:'18px', cursor:'pointer', flexShrink:0 },
  topTitle: { flex:1, fontSize:'17px', fontWeight:'600', color:'#1a1a2e' },
  inviteBtn: { width:'36px', height:'36px', borderRadius:'50%', background:'#EBF4FF', border:'none', fontSize:'18px', cursor:'pointer' },
  tabBar: { display:'flex', background:'#fff', borderTop:'1px solid #f0f0f0', borderBottom:'1px solid #f0f0f0', flexShrink:0 },
  tabBtn: { flex:1, padding:'10px 4px 8px', border:'none', background:'transparent', display:'flex', flexDirection:'column', alignItems:'center', gap:'2px', cursor:'pointer', fontSize:'10px', color:'#999' },
  tabActive: { color:'#378ADD', borderBottom:'2px solid #378ADD' },
  content: { flex:1, overflowY:'auto', padding:'14px' },
  dayLabel: { fontSize:'12px', fontWeight:'600', color:'#888', textTransform:'uppercase', letterSpacing:'.6px', marginBottom:'8px' },
  eventCard: { background:'#fff', borderRadius:'14px', padding:'12px 14px', marginBottom:'8px', display:'flex', gap:'10px', alignItems:'flex-start', border:'1px solid #eef2f7' },
  eventTime: { fontSize:'11px', color:'#888', minWidth:'36px', paddingTop:'2px' },
  eventDot: { width:'10px', height:'10px', borderRadius:'50%', marginTop:'4px', flexShrink:0 },
  eventTitle: { fontSize:'14px', fontWeight:'600', color:'#1a1a2e' },
  eventSub: { fontSize:'12px', color:'#888', marginTop:'2px' },
  eventNotes: { fontSize:'12px', color:'#aaa', marginTop:'2px', lineHeight:'1.5' },
  emptyState: { textAlign:'center', color:'#aaa', padding:'32px', fontSize:'14px' },
  addBtn: { width:'100%', padding:'12px', background:'transparent', border:'1.5px dashed #cdd5de', borderRadius:'14px', color:'#888', fontSize:'14px', cursor:'pointer', marginTop:'4px', marginBottom:'12px' },
  aiCard: { background:'#EBF4FF', borderRadius:'14px', padding:'12px 14px', borderLeft:'3px solid #378ADD', marginBottom:'16px' },
  aiLabel: { fontSize:'12px', fontWeight:'600', color:'#185FA5', marginBottom:'4px' },
  aiText: { fontSize:'13px', color:'#334', lineHeight:'1.5' },
  expSummary: { background:'linear-gradient(135deg,#378ADD,#185FA5)', borderRadius:'16px', padding:'18px 20px', marginBottom:'16px', color:'#fff' },
  expTotal: { fontSize:'28px', fontWeight:'700' },
  expSub: { fontSize:'13px', opacity:.85, marginTop:'2px' },
  expPer: { fontSize:'14px', fontWeight:'600', marginTop:'8px', opacity:.9 },
  sectionTitle: { fontSize:'12px', fontWeight:'600', color:'#888', textTransform:'uppercase', letterSpacing:'.5px', marginBottom:'8px', marginTop:'4px' },
  expItem: { background:'#fff', borderRadius:'14px', padding:'12px 14px', marginBottom:'8px', display:'flex', alignItems:'center', border:'1px solid #eef2f7' },
  expName: { fontSize:'14px', fontWeight:'600', color:'#1a1a2e' },
  expWho: { fontSize:'12px', color:'#888', marginTop:'2px' },
  expAmt: { fontSize:'15px', fontWeight:'700', color:'#378ADD' },
  chatWrap: { flex:1, display:'flex', flexDirection:'column', overflow:'hidden' },
  chatMessages: { flex:1, overflowY:'auto', padding:'14px', display:'flex', flexDirection:'column', gap:'10px' },
  msgWrap: { display:'flex', flexDirection:'column' },
  msgSender: { fontSize:'11px', color:'#888', marginBottom:'3px', paddingLeft:'4px' },
  bubble: { padding:'10px 13px', borderRadius:'16px', fontSize:'14px', lineHeight:1.4, maxWidth:'78%', wordBreak:'break-word' },
  bubbleIn: { background:'#f0f4f8', color:'#1a1a2e', borderBottomLeftRadius:'4px' },
  bubbleOut: { background:'#378ADD', color:'#fff', borderBottomRightRadius:'4px' },
  msgTime: { fontSize:'10px', color:'#bbb', marginTop:'3px', paddingLeft:'4px' },
  chatInput: { display:'flex', gap:'8px', padding:'10px 14px', background:'#fff', borderTop:'1px solid #f0f0f0' },
  chatInputField: { flex:1, padding:'10px 14px', background:'#f0f4f8', border:'none', borderRadius:'24px', fontSize:'14px', color:'#1a1a2e', outline:'none' },
  sendBtn: { width:'40px', height:'40px', background:'#378ADD', border:'none', borderRadius:'50%', display:'flex', alignItems:'center', justifyContent:'center', cursor:'pointer', flexShrink:0 },
  memberStats: { display:'grid', gridTemplateColumns:'1fr 1fr 1fr', gap:'8px', marginBottom:'16px' },
  statBox: { borderRadius:'12px', padding:'10px', textAlign:'center' },
  memberCard: { background:'#fff', borderRadius:'14px', padding:'12px 14px', marginBottom:'8px', display:'flex', alignItems:'center', gap:'12px', border:'1px solid #eef2f7' },
  memberAvatar: { width:'44px', height:'44px', borderRadius:'50%', display:'flex', alignItems:'center', justifyContent:'center', fontSize:'14px', fontWeight:'600', color:'#fff', flexShrink:0 },
  memberName: { fontSize:'14px', fontWeight:'600', color:'#1a1a2e' },
  memberRole: { fontSize:'12px', color:'#888', marginTop:'2px' },
  youBadge: { fontSize:'10px', background:'#EBF4FF', color:'#185FA5', padding:'2px 7px', borderRadius:'10px', fontWeight:'600', marginLeft:'6px' },
  actionBtn: { width:'30px', height:'30px', borderRadius:'8px', border:'none', fontSize:'14px', cursor:'pointer', display:'flex', alignItems:'center', justifyContent:'center' },
  inviteLinkCard: { background:'#f8fafc', border:'1px solid #eef2f7', borderRadius:'14px', padding:'12px 14px', marginTop:'12px' },
  inviteLinkLabel: { fontSize:'12px', fontWeight:'600', color:'#888', marginBottom:'6px' },
  inviteLinkText: { flex:1, fontSize:'12px', color:'#378ADD', background:'#EBF4FF', padding:'8px 10px', borderRadius:'8px', wordBreak:'break-all' },
  copyBtn: { padding:'8px 12px', background:'#378ADD', color:'#fff', border:'none', borderRadius:'8px', fontSize:'12px', fontWeight:'600', cursor:'pointer', flexShrink:0 },
  overlay: { position:'fixed', inset:0, background:'rgba(0,0,0,0.4)', display:'flex', alignItems:'flex-end', justifyContent:'center', zIndex:100 },
  modal: { background:'#fff', borderRadius:'24px 24px 0 0', padding:'24px', width:'100%', maxWidth:'430px', maxHeight:'85vh', overflowY:'auto' },
  handle: { width:'40px', height:'4px', background:'#e0e0e0', borderRadius:'2px', margin:'0 auto 20px' },
  modalTitle: { fontSize:'18px', fontWeight:'700', color:'#1a1a2e', marginBottom:'8px' },
  label: { fontSize:'13px', fontWeight:'600', color:'#555', marginBottom:'4px' },
  input: { width:'100%', padding:'12px 14px', border:'1.5px solid #e2e8f0', borderRadius:'12px', fontSize:'14px', color:'#1a1a2e', outline:'none', boxSizing:'border-box' },
  btnRow: { display:'flex', gap:'8px', marginTop:'8px' },
  cancelBtn: { flex:1, padding:'13px', background:'#f0f4f8', color:'#555', border:'none', borderRadius:'12px', fontSize:'14px', fontWeight:'600', cursor:'pointer' },
  saveBtn: { flex:1, padding:'13px', background:'#378ADD', color:'#fff', border:'none', borderRadius:'12px', fontSize:'14px', fontWeight:'600', cursor:'pointer' },
};