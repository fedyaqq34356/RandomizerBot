import json
import random
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional


class Storage:
    def __init__(self):
        self.data_dir = Path("data")
        self.data_dir.mkdir(exist_ok=True)
        
        self.user_accounts_file = self.data_dir / "user_accounts.json"
        self.giveaways_file = self.data_dir / "giveaways.json"
        self.participants_file = self.data_dir / "participants.json"
        self.winners_file = self.data_dir / "winners.json"
        
        self.user_accounts = self._load_json(self.user_accounts_file)
        self.giveaways = self._load_json(self.giveaways_file)
        self.participants = self._load_json(self.participants_file)
        self.winners = self._load_json(self.winners_file)
    
    def _load_json(self, file_path: Path) -> dict:
        if file_path.exists():
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def _save_json(self, data: dict, file_path: Path):
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def add_user_account(self, admin_id: int, session_name: str, phone: str, api_id: int, api_hash: str):
        admin_key = str(admin_id)
        if admin_key not in self.user_accounts:
            self.user_accounts[admin_key] = {}
        
        self.user_accounts[admin_key][session_name] = {
            "phone": phone,
            "api_id": api_id,
            "api_hash": api_hash
        }
        self._save_json(self.user_accounts, self.user_accounts_file)
    
    def remove_user_account(self, admin_id: int, session_name: str):
        admin_key = str(admin_id)
        if admin_key in self.user_accounts and session_name in self.user_accounts[admin_key]:
            del self.user_accounts[admin_key][session_name]
            self._save_json(self.user_accounts, self.user_accounts_file)
    
    def get_user_accounts(self, admin_id: int) -> Dict:
        admin_key = str(admin_id)
        return self.user_accounts.get(admin_key, {})
    
    def create_giveaway(self, admin_id: int, mode: str, text: str, button_text: str, 
                       channels: List[str], winners_count: int) -> str:
        giveaway_id = f"gw_{admin_id}_{datetime.now().timestamp()}"
        
        self.giveaways[giveaway_id] = {
            "admin_id": admin_id,
            "mode": mode,
            "text": text,
            "button_text": button_text,
            "channels": channels,
            "winners_count": winners_count,
            "created_at": datetime.now().isoformat(),
            "status": "active"
        }
        
        self.participants[giveaway_id] = []
        self.winners[giveaway_id] = []
        
        self._save_json(self.giveaways, self.giveaways_file)
        self._save_json(self.participants, self.participants_file)
        self._save_json(self.winners, self.winners_file)
        
        return giveaway_id
    
    def get_giveaway(self, giveaway_id: str) -> Optional[Dict]:
        return self.giveaways.get(giveaway_id)
    
    def get_admin_giveaways(self, admin_id: int) -> Dict:
        return {gid: data for gid, data in self.giveaways.items() if data["admin_id"] == admin_id}
    
    def delete_giveaway(self, giveaway_id: str):
        if giveaway_id in self.giveaways:
            del self.giveaways[giveaway_id]
            self._save_json(self.giveaways, self.giveaways_file)
        
        if giveaway_id in self.participants:
            del self.participants[giveaway_id]
            self._save_json(self.participants, self.participants_file)
        
        if giveaway_id in self.winners:
            del self.winners[giveaway_id]
            self._save_json(self.winners, self.winners_file)
    
    def add_participant(self, giveaway_id: str, username: str):
        if giveaway_id not in self.participants:
            self.participants[giveaway_id] = []
        
        if username not in self.participants[giveaway_id]:
            self.participants[giveaway_id].append(username)
            self._save_json(self.participants, self.participants_file)
            return True
        return False
    
    def get_participants(self, giveaway_id: str) -> List[str]:
        return self.participants.get(giveaway_id, [])
    
    def draw_winners(self, giveaway_id: str) -> List[str]:
        participants = self.get_participants(giveaway_id)
        giveaway = self.get_giveaway(giveaway_id)
        
        if not participants or not giveaway:
            return []
        
        winners_count = min(giveaway["winners_count"], len(participants))
        winners = random.sample(participants, winners_count)
        
        self.winners[giveaway_id] = winners
        self._save_json(self.winners, self.winners_file)
        
        return winners
    
    def get_winners(self, giveaway_id: str) -> List[str]:
        return self.winners.get(giveaway_id, [])


storage = Storage()
