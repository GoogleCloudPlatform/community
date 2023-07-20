enum JobTitle {
  'Analyst',
  'Associate Partner',
  'Client Delivery Lead',
  'Cloud Architect',
  'Cloud Engineer',
  'Partner',
  'Program Manager',
  'Project Manager',
  'Senior Cloud Architect',
  'Senior Cloud Engineer',
  'Senior Partner',
  'Senior Project Manager',
  'TBD'
}

interface Address {
  city: string;
  street: string;
}

export interface Employee {
  id?: string;
  firstName?: string;
  lastName?: string;
  jobTitle?: JobTitle;
  avatarURL?: string;
  imageURL?: string;
  yearsExperience?: number;
  address?: Address;
  displayName?: string;
  email?: string;
  authenticated?: boolean;
}

export interface DataInterface {
  currentEmployee: Employee;
}

export interface EmployeeCredentials {
  email: string;
  password: string;
}
