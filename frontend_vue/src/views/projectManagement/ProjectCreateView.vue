<template>
  <div class="project-create-view">
    <h1>Create New Project</h1>
    <form @submit.prevent="submitCreateProject" class="project-form">
      <div class="form-group">
        <label for="projectName">Project Name</label>
        <input type="text" id="projectName" v-model="project.name" class="form-control" required maxlength="100">
      </div>

      <div class="form-group">
        <label for="projectDescription">Description (Optional)</label>
        <textarea id="projectDescription" v-model="project.description" class="form-control" rows="3"></textarea>
      </div>

      <div class="form-group">
        <label for="projectStatus">Status</label>
        <select id="projectStatus" v-model="project.status" class="form-control">
          <option value="active">Active</option>
          <option value="inactive">Inactive</option>
          <option value="completed">Completed</option>
        </select>
      </div>

      <div v-if="error" class="error-message">
        <p>Error creating project: {{ error.message || error }}</p>
      </div>
      
      <div v-if="successMessage" class="success-message">
        <p>{{ successMessage }}</p>
      </div>

      <div class="form-actions">
        <button type="submit" class="btn btn-primary" :disabled="submitting">
          {{ submitting ? 'Creating...' : 'Create Project' }}
        </button>
        <button type="button" @click="goBack" class="btn btn-secondary" :disabled="submitting">
          Cancel
        </button>
      </div>
    </form>
  </div>
</template>

<script>
import axios from 'axios';

const PM_API_BASE_URL = '/pm_api'; // Matches the backend mount point

export default {
  name: 'ProjectCreateView',
  data() {
    return {
      project: {
        name: '',
        description: '',
        status: 'active', // Default status
      },
      submitting: false,
      error: null,
      successMessage: ''
    };
  },
  methods: {
    async submitCreateProject() {
      this.submitting = true;
      this.error = null;
      this.successMessage = '';
      try {
        const response = await axios.post(`${PM_API_BASE_URL}/projects/`, this.project);
        this.successMessage = `Project '${response.data.name}' created successfully! ID: ${response.data.id}`;
        // Optionally, reset form or redirect
        // this.resetForm();
        // this.$router.push({ name: 'ProjectDetail', params: { id: response.data.id } });
        setTimeout(() => {
            this.$router.push({ name: 'ProjectList' }); // Or to the detail page
        }, 1500); // Delay for user to see success message
      } catch (err) {
        console.error('Failed to create project:', err);
        this.error = err.response ? err.response.data : err;
        if (err.response && err.response.data && err.response.data.detail) {
            this.error = { message: err.response.data.detail };
        }
      }
      this.submitting = false;
    },
    resetForm() {
      this.project = {
        name: '',
        description: '',
        status: 'active',
      };
    },
    goBack() {
      this.$router.push({ name: 'ProjectList' }); // Or use this.$router.go(-1)
    }
  }
};
</script>

<style scoped>
.project-create-view {
  max-width: 600px;
  margin: 20px auto;
  padding: 20px;
  background-color: #f9f9f9;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.project-form .form-group {
  margin-bottom: 1.5rem;
}

.project-form label {
  display: block;
  margin-bottom: 0.5rem;
  font-weight: bold;
}

.project-form .form-control {
  width: 100%;
  padding: 0.5rem;
  font-size: 1rem;
  line-height: 1.5;
  border: 1px solid #ced4da;
  border-radius: 0.25rem;
  box-sizing: border-box; /* Ensures padding doesn't affect overall width */
}

.project-form textarea.form-control {
  resize: vertical;
}

.form-actions button {
  margin-right: 10px;
}

.error-message {
  color: #dc3545; /* Bootstrap's danger color */
  background-color: #f8d7da;
  border-color: #f5c6cb;
  padding: 0.75rem 1.25rem;
  margin-bottom: 1rem;
  border: 1px solid transparent;
  border-radius: 0.25rem;
}

.success-message {
  color: #155724; /* Bootstrap's success color */
  background-color: #d4edda;
  border-color: #c3e6cb;
  padding: 0.75rem 1.25rem;
  margin-bottom: 1rem;
  border: 1px solid transparent;
  border-radius: 0.25rem;
}

/* Basic Bootstrap-like styling for buttons if Bootstrap is not globally available */
.btn {
  display: inline-block;
  font-weight: 400;
  color: #212529;
  text-align: center;
  vertical-align: middle;
  cursor: pointer;
  user-select: none;
  background-color: transparent;
  border: 1px solid transparent;
  padding: 0.375rem 0.75rem;
  font-size: 1rem;
  line-height: 1.5;
  border-radius: 0.25rem;
  transition: color 0.15s ease-in-out, background-color 0.15s ease-in-out, border-color 0.15s ease-in-out, box-shadow 0.15s ease-in-out;
}

.btn-primary {
  color: #fff;
  background-color: #007bff;
  border-color: #007bff;
}

.btn-primary:hover {
  color: #fff;
  background-color: #0056b3;
  border-color: #0056b3;
}

.btn-primary:disabled {
  background-color: #007bff;
  border-color: #007bff;
  opacity: 0.65;
}

.btn-secondary {
  color: #fff;
  background-color: #6c757d;
  border-color: #6c757d;
}

.btn-secondary:hover {
  color: #fff;
  background-color: #545b62;
  border-color: #545b62;
}
</style>
