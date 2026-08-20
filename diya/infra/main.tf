terraform {
  required_version = ">= 1.5.0"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

variable "project_id" {
  description = "GCP project ID"
  type        = string
}

variable "region" {
  description = "GCP region"
  type        = string
  default     = "us-central1"
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# ── Enable Required APIs ─────────────────────────────────────────

resource "google_project_service" "apis" {
  for_each = toset([
    "run.googleapis.com",
    "firestore.googleapis.com",
    "pubsub.googleapis.com",
    "storage.googleapis.com",
    "aiplatform.googleapis.com",
    "cloudtrace.googleapis.com",
    "cloudbuild.googleapis.com",
    "artifactregistry.googleapis.com",
  ])

  service            = each.value
  disable_on_destroy = false
}

# ── Artifact Registry ─────────────────────────────────────────────

resource "google_artifact_registry_repository" "diya" {
  location      = var.region
  repository_id = "diya"
  format        = "DOCKER"
  description   = "DIYA container images"

  depends_on = [google_project_service.apis]
}

# ── Firestore ─────────────────────────────────────────────────────

resource "google_firestore_database" "default" {
  name        = "(default)"
  location_id = var.region
  type        = "FIRESTORE_NATIVE"

  depends_on = [google_project_service.apis]
}

# ── Cloud Storage (notices, OSM cache) ────────────────────────────

resource "google_storage_bucket" "notices" {
  name          = "${var.project_id}-diya-notices"
  location      = var.region
  force_destroy = true

  uniform_bucket_level_access = true
}

resource "google_storage_bucket" "osm_cache" {
  name          = "${var.project_id}-diya-osm-cache"
  location      = var.region
  force_destroy = true

  uniform_bucket_level_access = true
}

# ── Pub/Sub Topics ────────────────────────────────────────────────

resource "google_pubsub_topic" "department_feeds" {
  name = "diya-department-feeds"

  depends_on = [google_project_service.apis]
}

resource "google_pubsub_subscription" "department_feeds_sub" {
  name  = "diya-department-feeds-sub"
  topic = google_pubsub_topic.department_feeds.id

  ack_deadline_seconds = 60

  dead_letter_policy {
    dead_letter_topic     = google_pubsub_topic.department_feeds_dlq.id
    max_delivery_attempts = 5
  }
}

resource "google_pubsub_topic" "department_feeds_dlq" {
  name = "diya-department-feeds-dlq"

  depends_on = [google_project_service.apis]
}

resource "google_pubsub_topic" "conflict_events" {
  name = "diya-conflict-events"

  depends_on = [google_project_service.apis]
}

# ── Cloud Run Services ────────────────────────────────────────────

resource "google_cloud_run_v2_service" "api_gateway" {
  name     = "diya-api-gateway"
  location = var.region

  template {
    containers {
      image = "${var.region}-docker.pkg.dev/${var.project_id}/diya/api-gateway:latest"

      ports {
        container_port = 8000
      }

      env {
        name  = "MESH_SERVICE_URL"
        value = "https://diya-mesh-service-${data.google_project.project.number}.${var.region}.run.app"
      }

      env {
        name  = "AGENT_SERVICE_URL"
        value = "https://diya-agent-service-${data.google_project.project.number}.${var.region}.run.app"
      }

      env {
        name  = "NOTICE_SERVICE_URL"
        value = "https://diya-notice-service-${data.google_project.project.number}.${var.region}.run.app"
      }

      resources {
        limits = {
          cpu    = "1"
          memory = "512Mi"
        }
      }
    }

    scaling {
      min_instance_count = 0
      max_instance_count = 3
    }
  }

  depends_on = [google_project_service.apis]
}

resource "google_cloud_run_v2_service" "web" {
  name     = "diya-web"
  location = var.region

  template {
    containers {
      image = "${var.region}-docker.pkg.dev/${var.project_id}/diya/web:latest"

      ports {
        container_port = 3000
      }

      env {
        name  = "NEXT_PUBLIC_API_URL"
        value = google_cloud_run_v2_service.api_gateway.uri
      }

      resources {
        limits = {
          cpu    = "1"
          memory = "512Mi"
        }
      }
    }

    scaling {
      min_instance_count = 0
      max_instance_count = 3
    }
  }

  depends_on = [google_project_service.apis]
}

# ── IAM: Allow public access to web and API ───────────────────────

resource "google_cloud_run_v2_service_iam_member" "web_public" {
  name     = google_cloud_run_v2_service.web.name
  location = var.region
  role     = "roles/run.invoker"
  member   = "allUsers"
}

resource "google_cloud_run_v2_service_iam_member" "api_public" {
  name     = google_cloud_run_v2_service.api_gateway.name
  location = var.region
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# ── Data Source ────────────────────────────────────────────────────

data "google_project" "project" {}

# ── Outputs ───────────────────────────────────────────────────────

output "web_url" {
  value       = google_cloud_run_v2_service.web.uri
  description = "DIYA frontend URL"
}

output "api_url" {
  value       = google_cloud_run_v2_service.api_gateway.uri
  description = "DIYA API gateway URL"
}

output "notices_bucket" {
  value       = google_storage_bucket.notices.name
  description = "Cloud Storage bucket for citizen notices"
}
