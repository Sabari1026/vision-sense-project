import React, { createContext, useContext, useState, useEffect } from 'react';
import { UserProfile, UserRole } from '../types';

interface AuthContextType {
  user: UserProfile | null;
  role: UserRole;
  login: (email: string, role?: UserRole) => void;
  logout: () => void;
  setRole: (role: UserRole) => void;
}

const AuthContext = createContext<AuthContextType>({
  user: null,
  role: 'admin',
  login: () => {},
  logout: () => {},
  setRole: () => {},
});

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<UserProfile | null>({
    id: 'demo-user-1',
    email: 'admin@visionsense.ai',
    full_name: 'Sabari Kumar (Admin)',
    role: 'admin'
  });

  const [role, setRoleState] = useState<UserRole>('admin');

  const login = (email: string, selectRole: UserRole = 'admin') => {
    const newUser: UserProfile = {
      id: `user-${Date.now()}`,
      email,
      full_name: email.split('@')[0].toUpperCase(),
      role: selectRole
    };
    setUser(newUser);
    setRoleState(selectRole);
  };

  const logout = () => {
    setUser(null);
  };

  const setRole = (newRole: UserRole) => {
    setRoleState(newRole);
    if (user) {
      setUser({ ...user, role: newRole });
    }
  };

  return (
    <AuthContext.Provider value={{ user, role, login, logout, setRole }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);
