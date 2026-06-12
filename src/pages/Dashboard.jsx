import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { supabase } from '../supabaseClient';

export default function Dashboard({ session }) {
  const [trips, setTrips] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [newTrip, setNewTrip] = useState({ name:'', destination:'', start_date:'', end_date:'', emoji:'🌴' });
  const navigate = useNavigate();
  const user = session.user;
  const firstName = user.user_metadata?.name?.split(' ')[0] || 'Traveler';

  useEffect(() => { fetchTrips(); }, []);

  async function fetchTrips() {
    setLoading(true);
    const { data, error } = await supabase
      .from('trip_members')
      .select(`trip:trips(*)`)
      .eq('user_id', user.id);
    if (!error && data) setTrips(data.map(d => d.trip).filter(Boolean));
    setLoading(false);
  }

  async function createTrip() {
    if (!newTrip.name || !newTrip.destination) return alert('Please fill in trip name and destination.');
    const emojis = ['🌴','🏔️','🌊','🎭','🗺️','🏕️','🌍','🎪'];
    const emoji = emojis[Math.floor(Math.random() * emojis.length)];
    const colors = ['#378ADD','#1D9E75','#EF9F27','#D4537E','#7F77DD','#D85A30'];
    const cover_color = colors[Math.floor(Math.random() * colors.length)];

    const { data: trip, error: tripError } = await supabase
      .from('trips')
      .insert([{ ...newTrip, emoji, cover_color, created_by: user.id }])
      .select().single();

    if (tripError) return alert('Error creating trip: ' + tripError.message);

    await supabase.from('trip_members').insert([{
      trip_id: trip.id, user_id: user.id, status: 'accepted', role: 'organizer'
    }]);

    setShowModal(false);
    setNewTrip({ name:'', destination:'', start_date:'', end_date:'', emoji:'🌴' });
    fetchTrips();
  }

  async function signOut() {
    await supabase.auth.signOut();
  }

  const EMOJIS = ['🌴','🏔️','🌊','🎭','🗺️','🏕️','🌍','🎪','🏖️','🗽'];

  return (
    <div style={styles.container}>
      {/* Header */}
      <div style={styles.header}>
        <div>
          <div style={styles.greet}>Hey {firstName}! 👋</div>
          <div style={styles.sub}>{trips.length} trip{trips.length !== 1 ? 's' : ''} planned</div>
        </div>
        <button onClick={signOut} style={styles.signOutBtn}>Sign out</button>
      </div>

      {/* Trip list */}
      <div style={styles.list}>
        {loading ? (
          <div style={styles.empty}>Loading trips...</div>
        ) : trips.length === 0 ? (
          <div style={styles.emptyCard}>
            <div style={{fontSize:'48px',marginBottom:'12px'}}>🗺️</div>
            <div style={{fontSize:'16px',fontWeight:'600',color:'#1a1a2e',marginBottom:'6px'}}>No trips yet!</div>
            <div style={{fontSize:'13px',color:'#888'}}>Tap below to plan your first group trip</div>
          </div>
        ) : trips.map(trip => (
          <div key={trip.id} style={styles.card} onClick={() => navigate(`/trip/${trip.id}`)}>
            <div style={styles.cardHeader}>
              <div style={{...styles.emoji, background: trip.cover_color+'22'}}>{trip.emoji}</div>
              <div>
                <div style={styles.tripName}>{trip.name}</div>
                <div style={styles.tripDest}>📍 {trip.destination}</div>
              </div>
            </div>
            <div style={styles.badges}>
              {trip.start_date && <span style={styles.badge}>📅 {trip.start_date} → {trip.end_date}</span>}
            </div>
          </div>
        ))}

        <button style={styles.newTripBtn} onClick={() => setShowModal(true)}>
          ＋ &nbsp;Plan a new trip
        </button>
      </div>

      {/* New Trip Modal */}
      {showModal && (
        <div style={styles.overlay} onClick={e => e.target === e.currentTarget && setShowModal(false)}>
          <div style={styles.modal}>
            <div style={styles.handle} />
            <div style={styles.modalTitle}>Plan a new trip</div>

            <div style={styles.emojiRow}>
              {EMOJIS.map(em => (
                <span key={em} style={{...styles.emojiOpt, background: newTrip.emoji===em?'#EBF4FF':'#f0f4f8'}}
                  onClick={() => setNewTrip({...newTrip, emoji: em})}>{em}</span>
              ))}
            </div>

            <div style={styles.formGroup}>
              <div style={styles.label}>Trip name</div>
              <input style={styles.input} placeholder="e.g. Goa Family Trip"
                value={newTrip.name} onChange={e => setNewTrip({...newTrip, name: e.target.value})} />
            </div>
            <div style={styles.formGroup}>
              <div style={styles.label}>Destination</div>
              <input style={styles.input} placeholder="e.g. Goa, India"
                value={newTrip.destination} onChange={e => setNewTrip({...newTrip, destination: e.target.value})} />
            </div>
            <div style={{display:'flex', gap:'10px'}}>
              <div style={{...styles.formGroup, flex:1}}>
                <div style={styles.label}>Start date</div>
                <input style={styles.input} type="date"
                  value={newTrip.start_date} onChange={e => setNewTrip({...newTrip, start_date: e.target.value})} />
              </div>
              <div style={{...styles.formGroup, flex:1}}>
                <div style={styles.label}>End date</div>
                <input style={styles.input} type="date"
                  value={newTrip.end_date} onChange={e => setNewTrip({...newTrip, end_date: e.target.value})} />
              </div>
            </div>
            <div style={styles.btnRow}>
              <button style={styles.cancelBtn} onClick={() => setShowModal(false)}>Cancel</button>
              <button style={styles.saveBtn} onClick={createTrip}>Create trip ✈️</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

const styles = {
  container: { maxWidth:'430px', margin:'0 auto', minHeight:'100vh', background:'#f8fafc', display:'flex', flexDirection:'column' },
  header: { background:'#fff', padding:'20px 16px 16px', borderBottom:'1px solid #f0f0f0', display:'flex', justifyContent:'space-between', alignItems:'center' },
  greet: { fontSize:'22px', fontWeight:'700', color:'#1a1a2e' },
  sub: { fontSize:'13px', color:'#888', marginTop:'2px' },
  signOutBtn: { background:'#f0f4f8', border:'none', borderRadius:'10px', padding:'8px 14px', fontSize:'13px', color:'#555', cursor:'pointer' },
  list: { flex:1, padding:'16px', display:'flex', flexDirection:'column', gap:'12px' },
  empty: { textAlign:'center', color:'#888', padding:'40px', fontSize:'14px' },
  emptyCard: { background:'#fff', borderRadius:'16px', padding:'40px 24px', textAlign:'center', border:'1px solid #eef2f7' },
  card: { background:'#fff', borderRadius:'16px', padding:'16px', border:'1px solid #eef2f7', cursor:'pointer' },
  cardHeader: { display:'flex', alignItems:'center', gap:'12px', marginBottom:'10px' },
  emoji: { width:'44px', height:'44px', borderRadius:'12px', display:'flex', alignItems:'center', justifyContent:'center', fontSize:'22px', flexShrink:0 },
  tripName: { fontSize:'16px', fontWeight:'600', color:'#1a1a2e' },
  tripDest: { fontSize:'12px', color:'#888', marginTop:'2px' },
  badges: { display:'flex', gap:'8px', flexWrap:'wrap' },
  badge: { fontSize:'11px', background:'#f0f4f8', color:'#555', padding:'4px 10px', borderRadius:'20px' },
  newTripBtn: { width:'100%', padding:'14px', background:'linear-gradient(135deg,#378ADD,#185FA5)', color:'#fff', border:'none', borderRadius:'16px', fontSize:'15px', fontWeight:'600', cursor:'pointer' },
  overlay: { position:'fixed', inset:0, background:'rgba(0,0,0,0.4)', display:'flex', alignItems:'flex-end', justifyContent:'center', zIndex:100 },
  modal: { background:'#fff', borderRadius:'24px 24px 0 0', padding:'24px', width:'100%', maxWidth:'430px' },
  handle: { width:'40px', height:'4px', background:'#e0e0e0', borderRadius:'2px', margin:'0 auto 20px' },
  modalTitle: { fontSize:'18px', fontWeight:'700', color:'#1a1a2e', marginBottom:'16px' },
  emojiRow: { display:'flex', flexWrap:'wrap', gap:'8px', marginBottom:'16px' },
  emojiOpt: { fontSize:'22px', padding:'6px', borderRadius:'10px', cursor:'pointer' },
  formGroup: { marginBottom:'12px' },
  label: { fontSize:'13px', fontWeight:'600', color:'#555', marginBottom:'4px' },
  input: { width:'100%', padding:'12px 14px', border:'1.5px solid #e2e8f0', borderRadius:'12px', fontSize:'14px', color:'#1a1a2e', outline:'none', boxSizing:'border-box' },
  btnRow: { display:'flex', gap:'8px', marginTop:'8px' },
  cancelBtn: { flex:1, padding:'13px', background:'#f0f4f8', color:'#555', border:'none', borderRadius:'12px', fontSize:'14px', fontWeight:'600', cursor:'pointer' },
  saveBtn: { flex:1, padding:'13px', background:'#378ADD', color:'#fff', border:'none', borderRadius:'12px', fontSize:'14px', fontWeight:'600', cursor:'pointer' },
};